from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from .models import User
# from referral.models import ReferralAccount
from .utils import generate_referral_code

@receiver(pre_save, sender=User)
def ensure_referral_code(sender, instance, **kwargs):
    """
    If model contains a referral_code field, ensure it's set.
    """
    if hasattr(instance, 'referral_code') and not instance.referral_code:
        instance.referral_code = generate_referral_code()


@receiver(post_save, sender=User)
def create_related_accounts(sender, instance, created, **kwargs):
    if not created:
        return

    # ✅ create wallet if payments app available
    try:
        from payments.models import Wallet
        if getattr(instance, 'wallet', None) is None:
            wallet = Wallet.objects.create(user=instance)
            instance.wallet = wallet
    except Exception:
        # payment app missing or create fails; ignore safely
        pass

    # ❌ referral app not ready yet — comment out for now
    """
    try:
        from referral.models import ReferralAccount
        if getattr(instance, 'referral', None) is None:
            code = getattr(instance, 'referral_code', None) or generate_referral_code()
            ref = ReferralAccount.objects.create(user=instance, code=code)
            instance.referral = ref
    except Exception:
        pass
    """

    # update instance if links set
    try:
        instance.save()
    except Exception:
        # avoid infinite loop
        pass
