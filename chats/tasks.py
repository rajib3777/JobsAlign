from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Message

@shared_task
def send_message_notifications(message_id):
    try:
        msg = Message.objects.select_related('conversation').get(id=message_id)
    except Message.DoesNotExist:
        return False
    participants = msg.conversation.participants.exclude(user=msg.sender)
    emails = [p.user.email for p in participants if getattr(p.user, 'email', None)]
    if emails:
        send_mail(
            subject=f"New message in {msg.conversation}",
            message=(msg.content or "You have a new message."),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=emails,
            fail_silently=True,
        )
    return True
