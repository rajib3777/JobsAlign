from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification
import time
import json

@shared_task(bind=True, default_retry_delay=30, max_retries=3)
def deliver_push_notification(self, notification_id):
    """
    Placeholder for push provider integration (FCM/APNs).  
    On success mark Notification.is_push_sent True.
    """
    try:
        notif = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return False

    # Example: build payload
    payload = {
        'title': notif.title,
        'body': notif.message or notif.title,
        'data': notif.data or {}
    }

    # TODO: integrate with real push service using user's device tokens (stored elsewhere)
    # For now simulate a send delay
    try:
        time.sleep(0.2)
        notif.is_push_sent = True
        notif.save(update_fields=['is_push_sent'])
        return True
    except Exception as exc:
        raise self.retry(exc=exc)

@shared_task(bind=True, default_retry_delay=30, max_retries=3)
def send_email_notification(self, notification_id):
    """
    Sends a simple transactional email about the notification.
    For production use templating (Django templates or external transactional service).
    """
    try:
        notif = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return False

    # build a simple subject/body
    subject = notif.title
    body = notif.message or ''
    recipient = getattr(notif.user, 'email', None)
    if not recipient:
        return False
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
        return True
    except Exception as exc:
        raise self.retry(exc=exc)
    



def get_create_notification():
    from notifications.utils import create_notification
    return create_notification
