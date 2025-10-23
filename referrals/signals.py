from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from django.contrib.auth import get_user_model
User = get_user_model()

from .models import Referral, ReferralCode
from .utils import create_referral_code_for_user, get_client_ip
from django.utils import timezone

# Hook: create referral code when user created
@receiver(post_save, sender=User)
def ensure_referral_code(sender, instance, created, **kwargs):
    if created:
        try:
            create_referral_code_for_user(instance)
        except Exception:
            pass

# Hook: listen to payments.Transaction creation to auto-calc commission.
# We try to import Transaction from payments.models; if not present, this listener will be a no-op.
try:
    from payments.models import Transaction
    from .utils import calculate_referral_commission_for_transaction

    @receiver(post_save, sender=Transaction)
    def on_transaction_created(sender, instance, created, **kwargs):
        """
        When a transaction occurs (e.g. payment from buyer), calculate referral commission.
        Only act for relevant transaction types (e.g., 'payment' or 'escrow_release', adjust to your model)
        """
        if not created:
            return
        tx_type = getattr(instance, "type", "").lower()
        # adjust types as per your payments app: 'payment', 'deposit', 'withdrawal' etc.
        if tx_type in ["payment", "deposit", "charge"]:
            try:
                calculate_referral_commission_for_transaction(instance)
            except Exception:
                # swallow exceptions to avoid breaking payment flow
                pass
except Exception:
    # payments app not found or Transaction missing — skip signal
    pass
