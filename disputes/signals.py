from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Dispute
from . import utils

@receiver(post_save, sender=Dispute)
def on_dispute_created(sender, instance, created, **kwargs):
    if created:
        # freeze escrow
        try:
            frozen = utils.freeze_escrow_for_dispute(instance)
            utils.log_timeline(instance, instance.opener, 'opened', {'frozen': bool(frozen)})
            # create dispute chat
            utils.create_dispute_chat(instance)
        except Exception:
            utils.log_timeline(instance, None, 'open_failed', {})
