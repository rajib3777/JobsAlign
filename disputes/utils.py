from django.db import transaction
from django.conf import settings
from django.utils import timezone
from .models import Dispute, DisputeTimeline
from notifications import utils as notif_utils

def log_timeline(dispute, actor, verb, payload=None):
    DisputeTimeline.objects.create(dispute=dispute, actor=actor, verb=verb, payload=payload or {})
    # optional quick notification
    try:
        notif_utils.create_notification(
            user=dispute.opener,
            verb='dispute_update',
            title=f"Dispute {dispute.id} updated",
            message=f"{verb}",
            data={'dispute_id': str(dispute.id)}
        )
    except Exception:
        pass

def freeze_escrow_for_dispute(dispute):
    """
    Ask payments app to freeze escrow for the contract.
    Implemented via payments.utils (must provide create_escrow_lock or similar).
    """
    try:
        from payments import utils as pay_utils
        # try to create a freeze record
        return pay_utils.freeze_escrow_for_contract(dispute.contract, reason=f"Dispute {dispute.id}")
    except Exception:
        return False

def unfreeze_escrow_for_dispute(dispute, release_to):  # release_to: 'buyer'|'freelancer'|'split'
    try:
        from payments import utils as pay_utils
        return pay_utils.resolve_escrow_for_dispute(dispute.contract, dispute, release_to=release_to)
    except Exception:
        return False

def create_dispute_chat(dispute):
    """
    Create or link a chat conversation for dispute discussion for audit.
    """
    try:
        from chats.utils import create_conversation_for_contract
        conv = create_conversation_for_contract(dispute.contract)  # this returns existing conv or new
        # Post a system message into the conversation
        from chats import utils as chats_utils
        chats_utils.post_system_message(conv, f"Dispute opened: {dispute.reason}")
        return conv
    except Exception:
        return None
