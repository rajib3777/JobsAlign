from celery import shared_task
from .models import Referral, ReferralCommission
from . import utils
from django.utils import timezone
from decimal import Decimal

@shared_task(bind=True)
def process_pending_referral_commissions(self, batch=100):
    """
    Check for commissions created but not credited/paid (if you use a payout step).
    This job can verify transactions settlement status and mark paid.
    """
    qs = ReferralCommission.objects.filter(paid=False).order_by("created_at")[:batch]
    for c in qs:
        try:
            # Optional: verify transaction settled/cleared in payments system before marking paid.
            # Here we simply mark paid = True (or keep workflow to payout later)
            c.paid = True
            c.save(update_fields=["paid"])
        except Exception:
            continue
    return True
