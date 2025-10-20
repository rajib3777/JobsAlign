from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Notification, NotificationPreference
from . import utils

# Example integrations: connect to other apps' signals.
# Marketplace -> create notification when contract completed (example)
try:
    from marketplace.models import Contract
    @receiver(post_save, sender=Contract)
    def on_contract_updated(sender, instance, created, **kwargs):
        # only notify when status becomes completed
        if not created and getattr(instance, 'is_active', True) and getattr(instance, 'completed_at', None):
            try:
                # buyer and freelancer both notified
                utils.create_notification(
                    user=instance.buyer,
                    verb='contract_completed',
                    title='Contract completed',
                    message=f'Your contract "{instance.project.title}" has been marked completed.',
                    data={'contract_id': str(instance.id)},
                    group_key=f'contract_completed:{instance.id}'
                )
                utils.create_notification(
                    user=instance.freelancer,
                    verb='contract_completed',
                    title='Contract completed',
                    message=f'Contract "{instance.project.title}" is completed. Leave a review.',
                    data={'contract_id': str(instance.id)},
                    group_key=f'contract_completed:{instance.id}'
                )
            except Exception:
                pass
except ImportError:
    pass

# Reviews integration
try:
    from reviews.models import Review
    @receiver(post_save, sender=Review)
    def on_review_created(sender, instance, created, **kwargs):
        if created:
            try:
                utils.create_notification(
                    user=instance.reviewee,
                    actor=instance.reviewer,
                    verb='new_review',
                    title='You received a new review',
                    message=f'{instance.reviewer} rated you {instance.rating}★',
                    data={'review_id': str(instance.id)}
                )
            except Exception:
                pass
except ImportError:
    pass

# Payments integration: transaction success (example)
try:
    from payments.models import Transaction
    @receiver(post_save, sender=Transaction)
    def on_transaction_updated(sender, instance, created, **kwargs):
        # notify user on successful deposit/withdrawal
        if not created and instance.status == 'success':
            try:
                utils.create_notification(
                    user=instance.user,
                    verb='transaction_success',
                    title=f'Payment {instance.type} succeeded',
                    message=f'Your {instance.type} of {instance.amount} {instance.gateway or ""} completed.',
                    data={'transaction_id': str(instance.id)}
                )
            except Exception:
                pass
except ImportError:
    pass

# Chats integration: when a new message is created, some apps prefer a notification in notifications table
try:
    from chats.models import Message
    @receiver(post_save, sender=Message)
    def on_message_created(sender, instance, created, **kwargs):
        if created and instance.sender:
            # notify other participants
            try:
                for p in instance.conversation.participants.exclude(user=instance.sender):
                    utils.create_notification(
                        user=p.user,
                        actor=instance.sender,
                        verb='new_message',
                        title=f'New message from {instance.sender.full_name}',
                        message=instance.content or 'You received a new message',
                        data={'conversation_id': str(instance.conversation_id), 'message_id': str(instance.id)},
                        group_key=f'chat_unread:{instance.conversation_id}:{p.user.id}'
                    )
            except Exception:
                pass
except ImportError:
    pass
