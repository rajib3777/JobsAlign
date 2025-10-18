from django.apps import apps
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from .models import ProjectActivityLog

def calculate_commission(amount):
    # platform commission (example: 10%)
    percent = Decimal(getattr(settings, "PLATFORM_COMMISSION_PERCENT", "10.0"))
    fee = (Decimal(amount) * (percent / Decimal("100.0"))).quantize(Decimal("0.01"))
    return fee

def enqueue_suggested_bid(bid):
    # placeholder: enqueue background job to compute suggested bid using AI/ML
    # implement Celery task later
    try:
        from .tasks import compute_suggested_bid  # celery task
        compute_suggested_bid.delay(str(bid.id))
    except Exception:
        # fallback quick heuristic
        bid.suggested_by_ai = {"price": float(bid.amount), "note":"heuristic"}
        bid.save(update_fields=["suggested_by_ai"])


def create_escrow_for_contract(contract):
    """
    Create escrow/transaction via payments app.
    We use apps.get_model to avoid circular import.
    """
    try:
        payments_utils = apps.get_app_config("payments").module.utils
    except Exception:
        payments_utils = None

    # create transaction record & call payment initiation if payments utils present
    if payments_utils and hasattr(payments_utils, "create_escrow_for_contract"):
        return payments_utils.create_escrow_for_contract(contract)
    # fallback: return placeholder reference
    return f"ESCROW-{contract.id}"

def release_milestone_payment(contract, milestone):
    try:
        payments_utils = apps.get_app_config("payments").module.utils
    except Exception:
        payments_utils = None

    if payments_utils and hasattr(payments_utils, "release_milestone"):
        return payments_utils.release_milestone(contract, milestone)
    return False

def log_activity(project, actor, action, meta=None):
    ProjectActivityLog.objects.create(project=project, actor=actor, action=action, meta=meta or {})
