from django.db.models.signals import post_save
from django.dispatch import receiver
from marketplace.models import Contract
from .models import Conversation, Message
from django.conf import settings

@receiver(post_save, sender=Contract)
def create_conversation_on_contract(sender, instance, created, **kwargs):
    if created:
        conv = Conversation.objects.create(project=instance.project, contract=instance)
        conv.participants.set([instance.buyer.id, instance.freelancer.id])
        # system message to notify
        Message.objects.create(conversation=conv, is_system=True, text=f"📝 Contract created between {instance.buyer.full_name} and {instance.freelancer.full_name} for {instance.project.title}.")

# Payments integration: payments.utils should call chat_notify_release(contract, milestone)
def chat_notify_release(contract, milestone):
    try:
        conv = getattr(contract, "conversation", None)
        if conv:
            Message.objects.create(conversation=conv, is_system=True, text=f"💰 Payment released: {milestone.amount} {contract.project.currency}.")
    except Exception:
        pass
