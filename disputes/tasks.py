from celery import shared_task
from django.utils import timezone
from .models import Dispute
from . import utils
from django.conf import settings

@shared_task(bind=True)
def auto_escalate_disputes(self):
    
    now = timezone.now()
    due = Dispute.objects.filter(status__in=['open','under_review','mediation'], sla_deadline__lte=now)
    for d in due:
        try:
            d.status = 'escalated'
            d.save(update_fields=['status','updated_at'])
            utils.log_timeline(d, None, 'auto_escalated', {'reason':'sla_missed'})
            # notify admins / moderator queue
            from notifications.utils import create_notification
            create_notification(
                user=None,  # sending to admin queue - implement admin group handling
                verb='dispute_escalated',
                title='Dispute escalated',
                message=f'Dispute {d.id} escalated due to SLA miss',
                data={'dispute_id': str(d.id)}
            )
        except Exception:
            continue

@shared_task(bind=True)
def summarize_evidence(self, dispute_id):
    """
    Example ML summarizer hook. Replace with actual model or external API.
    """
    try:
        d = Dispute.objects.get(id=dispute_id)
    except Dispute.DoesNotExist:
        return False
    # collect text from evidence
    texts = [e.text for e in d.evidences.exclude(text__isnull=True).values_list('text', flat=True)]
    # placeholder: naive join and truncate; replace this with call to OpenAI/transformer
    summary = ' '.join(texts)[:2000]
    # store in timeline
    utils.log_timeline(d, None, 'evidence_summarized', {'summary': summary})
    return summary
