from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TicketMessage, SupportTicket, SupportAudit
from notifications.utils import create_notification

@receiver(post_save, sender=TicketMessage)
def on_new_ticket_message(sender, instance, created, **kwargs):
    if not created:
        return
    ticket = instance.ticket
    # if internal message, notify assigned agent(s) only
    if instance.internal:
        if ticket.assigned_to:
            create_notification(user=ticket.assigned_to, verb='ticket_internal_note', title=f'Internal note on {ticket.subject}', message=instance.content[:200], data={'ticket_id': str(ticket.id)})
        return
    # for user-visible messages
    if instance.system:
        # system messages -> notify user
        create_notification(user=ticket.user, verb='ticket_system_message', title=f'Update on: {ticket.subject}', message=instance.content[:200], data={'ticket_id': str(ticket.id)})
        return
    # If sender is agent, notify user
    if instance.sender and (instance.sender.is_staff or getattr(instance.sender, 'is_support_agent', False)):
        create_notification(user=ticket.user, verb='ticket_reply', title=f'Reply on: {ticket.subject}', message=instance.content[:200], data={'ticket_id': str(ticket.id)})
    else:
        # user replied -> notify agent or admin group
        if ticket.assigned_to:
            create_notification(user=ticket.assigned_to, verb='new_message', title=f'New message on {ticket.subject}', message=instance.content[:200], data={'ticket_id': str(ticket.id)})
        else:
            create_notification(user=None, verb='new_message', title=f'New message on {ticket.subject}', message=instance.content[:200], data={'ticket_id': str(ticket.id)})
    SupportAudit.objects.create(ticket=ticket, actor=instance.sender, verb='message_created', payload={'msg_id': str(instance.id)})
