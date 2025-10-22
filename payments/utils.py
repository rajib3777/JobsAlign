from .models import Transaction
import uuid

from .models import Escrow, Wallet
from marketplace.models import Contract
from decimal import Decimal
from django.apps import apps


# ✅ ✅ ✅ --- CHATS INTEGRATION ---
def send_payment_system_message(contract, text):
    """
    Send a system message to the chat conversation related to this contract.
    """
    try:
        Conversation = apps.get_model('chats', 'Conversation')
        Message = apps.get_model('chats', 'Message')

        # contract.id এর মাধ্যমে relevant chat conversation খোঁজা
        conv = Conversation.objects.filter(title__icontains=str(contract.id)).first()
        if not conv:
            return None

        # sender=None মানে এটা system message
        Message.objects.create(
            conversation=conv,
            sender=None,
            content=text
        )
    except Exception as e:
        print(f"[Chats Integration] Payment system message failed: {e}")
# ✅ ✅ ✅ --- END CHATS INTEGRATION ---


def initiate_payment_gateway(user, gateway, amount):
    reference = f"{gateway.name.upper()}-{uuid.uuid4().hex[:8]}"
    transaction = Transaction.objects.create(
        user=user,
        gateway=gateway,
        type="deposit",
        amount=amount,
        reference=reference
    )
    
    return {
        "transaction_id": str(transaction.id),
        "reference": reference,
        "gateway": gateway.name,
        "redirect_url": f"/payments/{gateway.name.lower()}/checkout/{reference}/"
    }


def initiate_escrow_payment(buyer, project, amount, method="stripe"):
    """
    Handle buyer payment during project creation.
    """
    try:
        if method == "stripe":
            from gateway_services.stripe_gateway import create_stripe_payment
            result = create_stripe_payment(buyer, amount)
        elif method == "sslcommerz":
            from gateway_services.sslcommerz import create_ssl_payment
            result = create_ssl_payment(buyer, amount)
        elif method == "bkash":
            from gateway_services.bkash import create_bkash_payment
            result = create_bkash_payment(buyer, amount)
        elif method == "paypal":
            from gateway_services.paypal_gateway import create_paypal_payment
            result = create_paypal_payment(buyer, amount)
        else:
            return {"success": False, "error": "Unsupported method"}

        if not result.get("success"):
            return result

        escrow = Escrow.objects.create(
            contract=None,
            buyer=buyer,
            freelancer=None,
            amount=Decimal(amount),
            status="held",
        )

        project.escrow_reference = f"ESCROW-{escrow.id}"
        project.save()

        return {"success": True, "escrow_id": escrow.id}

    except Exception as e:
        return {"success": False, "error": str(e)}


# ✅ ✅ ✅ --- ADDITIONAL CHATS INTEGRATION (SAFE ADDITION) ---
def release_milestone(contract, milestone):
    """
    Release escrow for a milestone and notify chat participants.
    """
    try:
        # এখানে সাধারণত আসল পেমেন্ট রিলিজ লজিক থাকবে (তুমি চাইলে future gateway call বসাতে পারো)
        milestone.status = "paid"
        milestone.save(update_fields=["status"])

        # 💬 system message পাঠানো (chat integration)
        send_payment_system_message(
            contract,
            f"💰 Milestone '{milestone.title}' approved — ৳{milestone.amount} released."
        )

        return True
    except Exception as e:
        print(f"[Payments Integration] Milestone release failed: {e}")
        return False
# ✅ ✅ ✅ --- END ADDITIONAL CHATS INTEGRATION ---


# ✅ ✅ ✅ --- DISPUTES INTEGRATION (ENTERPRISE-LEVEL, SAFE ADDITION) ---
from django.utils import timezone

def freeze_escrow_for_contract(contract, reason=None):
    """
    Freeze escrow funds when a dispute is opened.
    Used by disputes app.
    """
    try:
        escrow = getattr(contract, "escrow", None)
        if not escrow:
            # optional fallback: search by contract.id reference
            escrow = Escrow.objects.filter(contract_id=contract.id).first()
        if not escrow:
            print(f"[Disputes Integration] No escrow found for contract {contract.id}")
            return False

        escrow.is_frozen = True
        escrow.meta = {**(getattr(escrow, "meta", {}) or {}), "freeze_reason": reason or "dispute_opened"}
        escrow.save(update_fields=["is_frozen", "meta"])
        
        # 💬 system message
        send_payment_system_message(contract, f"⚠️ Escrow temporarily frozen due to dispute.")
        return True
    except Exception as e:
        print(f"[Disputes Integration] Escrow freeze failed: {e}")
        return False


def resolve_escrow_for_dispute(contract, dispute, release_to="freelancer"):
    """
    Unfreeze and resolve escrow funds based on dispute outcome.
    release_to: 'buyer' | 'freelancer' | 'split'
    """
    try:
        escrow = getattr(contract, "escrow", None)
        if not escrow:
            escrow = Escrow.objects.filter(contract_id=contract.id).first()
        if not escrow:
            print(f"[Disputes Integration] No escrow found for resolution: {contract.id}")
            return False

        # Release decision logic
        if release_to in ("freelancer", "freelancer_wins"):
            escrow.status = "released"
            escrow.released_at = timezone.now()
            escrow.is_frozen = False
            escrow.save(update_fields=["status", "released_at", "is_frozen"])
            send_payment_system_message(contract, "✅ Dispute resolved — funds released to Freelancer.")
        
        elif release_to in ("buyer", "buyer_wins"):
            escrow.status = "refunded"
            escrow.released_at = timezone.now()
            escrow.is_frozen = False
            escrow.save(update_fields=["status", "released_at", "is_frozen"])
            send_payment_system_message(contract, "💸 Dispute resolved — funds refunded to Buyer.")
        
        elif release_to == "split":
            escrow.status = "split_resolved"
            escrow.released_at = timezone.now()
            escrow.is_frozen = False
            escrow.save(update_fields=["status", "released_at", "is_frozen"])
            send_payment_system_message(contract, "⚖️ Dispute resolved — funds split between Buyer & Freelancer.")
        
        else:
            print(f"[Disputes Integration] Invalid release_to option: {release_to}")
            return False

        return True
    except Exception as e:
        print(f"[Disputes Integration] Escrow resolve failed: {e}")
        return False
# ✅ ✅ ✅ --- END DISPUTES INTEGRATION ---
