from celery import shared_task
from django.utils import timezone
from .models import SupportTicket, TicketMessage, SupportAudit
from . import utils
from notifications.utils import create_notification

@shared_task(bind=True)
def classify_and_tag_ticket(self, ticket_id):
    """
    Run intent classification and priority suggestion (invoked on ticket creation).
    """
    try:
        ticket = SupportTicket.objects.get(id=ticket_id)
    except SupportTicket.DoesNotExist:
        return

    try:
        intent, priority = utils.classify_ticket_intent(ticket.subject + " " + (ticket.meta.get('body','') if ticket.meta else ''))
        # set priority if suggested is higher than current
        if priority and priority in ['low','medium','high','urgent']:
            ticket.priority = priority
        ticket.meta = {**(ticket.meta or {}), 'intent': intent}
        ticket.save(update_fields=['priority','meta','updated_at'])
        SupportAudit.objects.create(ticket=ticket, actor=None, verb='classified_ticket', payload={'intent': intent, 'priority': priority})
        # if urgent, notify support admins
        if priority == 'urgent':
            create_notification(user=None, verb='urgent_ticket', title='Urgent ticket', message=f'Ticket {ticket.subject} flagged urgent', data={'ticket_id': str(ticket.id)})
    except Exception as e:
        SupportAudit.objects.create(ticket=ticket, actor=None, verb='classification_failed', payload={'error': str(e)})

@shared_task(bind=True)
def auto_respond_low_priority(self, hours_threshold=2):
    """
    Auto-respond simple low-priority tickets using canned responses / AI bot.
    """
    cutoff = timezone.now() - timezone.timedelta(hours=hours_threshold)
    qs = SupportTicket.objects.filter(status='open', priority='low', updated_at__lte=cutoff)
    for t in qs:
        try:
            # get reply from utils (AI or canned)
            reply = utils.generate_auto_reply(t)
            if reply:
                msg = TicketMessage.objects.create(ticket=t, sender=None, content=reply, system=True)
                SupportAudit.objects.create(ticket=t, actor=None, verb='auto_responded', payload={'reply': reply})
                t.status = 'pending_user'
                t.save(update_fields=['status','updated_at'])
                create_notification(user=t.user, verb='ticket_auto_reply', title='Support response', message=reply[:200], data={'ticket_id': str(t.id)})
        except Exception as e:
            SupportAudit.objects.create(ticket=t, actor=None, verb='auto_reply_failed', payload={'error': str(e)})

@shared_task(bind=True)
def escalate_stalled_tickets(self, days=3):
    """
    Escalate tickets that are open without agent response for N days.
    """
    cutoff = timezone.now() - timezone.timedelta(days=days)
    qs = SupportTicket.objects.filter(status__in=['open','pending_agent'], updated_at__lte=cutoff)
    for t in qs:
        t.status = 'escalated'
        t.save(update_fields=['status','updated_at'])
        SupportAudit.objects.create(ticket=t, actor=None, verb='escalated', payload={})
        create_notification(user=None, verb='ticket_escalated', title='Ticket escalated', message=f'Ticket {t.subject} escalated', data={'ticket_id': str(t.id)})
