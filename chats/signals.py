from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message
from .utils import notify_message_created

@receiver(post_save, sender=Message)
def on_message_created(sender, instance, created, **kwargs):
    if created:
        try:
            notify_message_created(instance)
        except Exception:
            pass
