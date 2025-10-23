import secrets
from decimal import Decimal
from django.utils.text import slugify
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from .models import ReferralCode, Referral, ReferralCommission
from notifications.utils import create_notification


try:
    from payments.models import Wallet
except Exception:
    Wallet = None  # fallback; integrate accordingly


DEFAULT_COMMISSION_PERCENT = Decimal(getattr(settings, "REFERRAL_COMMISSION_PERCENT", "2.00"))

def generate_referral_code(username):
    
    base = slugify(username)[:6].upper()
    token = secrets.token_hex(2).upper()
    code = f"{base}{token}"
    # avoid collision
    if ReferralCode.objects.filter(code=code).exists():
        return generate_referral_code(username + secrets.token_hex(1))
    return code

def create_referral_code_for_user(user):
    
    rc, created = ReferralCode.objects.get_or_create(user=user, defaults={"code": generate_referral_code(user.username)})
    return rc

def get_referrer_for_code(code):
    try:
        rc = ReferralCode.objects.get(code=code)
        return rc.user
    except ReferralCode.DoesNotExist:
        return None

def attach_referral_from_request(request, user):
    
    code = request.GET.get("ref") or request.POST.get("referral_code") or request.session.get("signup_referral_code")
    if not code:
        return None
    try:
        from .models import ReferralCode, Referral
        rc = ReferralCode.objects.filter(code=code).first()
        if not rc:
            return None
        # prevent self-referral
        if rc.user.id == user.id:
            return None
        Referral.objects.create(
            referrer=rc.user,
            referred=user,
            code_used=rc.code,
            ip_address=get_client_ip(request),
            device_fingerprint=request.META.get("HTTP_X_DEVICE_FINGERPRINT",""),
            created_at=timezone.now()
        )
        rc.total_signups = rc.total_signups + 1
        rc.save(update_fields=["total_signups"])
        return rc
    except Exception:
        return None

def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

def calculate_referral_commission_for_transaction(transaction, percent: Decimal = None):
    
    percent = percent if percent is not None else DEFAULT_COMMISSION_PERCENT
    # transaction.user is the payer / user who triggered the transaction
    user = getattr(transaction, "user", None)
    if not user:
        return None

    
    referral = getattr(user, "referred_by", None) or getattr(user, "referral", None)
    
    try:
        from .models import Referral
        referral = Referral.objects.filter(referred=user).order_by("-created_at").first()
    except Exception:
        referral = None

    if not referral:
        return None

    
    try:
        tx_ip = getattr(transaction, "ip_address", None)
        if tx_ip and referral.ip_address and tx_ip == referral.ip_address:
            # mark suspect; do not pay automatically
            # create zero commission with metadata
            rc = ReferralCommission.objects.create(
                referral=referral,
                transaction_id=str(transaction.id),
                base_amount=getattr(transaction, "amount", Decimal("0.00")),
                percentage=percent,
                earned_amount=Decimal("0.00"),
                metadata={"reason":"ip_match_suspected"}
            )
            return rc
    except Exception:
        pass

    
    amount = Decimal(getattr(transaction, "amount", 0)) or Decimal("0.00")
    if amount <= 0:
        return None
    commission_amount = (amount * Decimal(percent)) / Decimal("100.00")
    commission_amount = commission_amount.quantize(Decimal("0.01"))

    # create commission record
    rc = ReferralCommission.objects.create(
        referral=referral,
        transaction_id=str(transaction.id),
        base_amount=amount,
        percentage=percent,
        earned_amount=commission_amount,
        metadata={"auto_created": True}
    )

    
    try:
        if Wallet:
            wallet, _ = Wallet.objects.get_or_create(user=referral.referrer)
            wallet.balance = (wallet.balance or Decimal("0.00")) + commission_amount
            wallet.save(update_fields=["balance"])
    except Exception:
        # do not fail the pipeline
        pass

    
    referral.total_commission = (referral.total_commission or Decimal("0.00")) + commission_amount
    referral.save(update_fields=["total_commission"])

    
    try:
        rc_obj = ReferralCode.objects.filter(user=referral.referrer).first()
        if rc_obj:
            rc_obj.total_earnings = (rc_obj.total_earnings or Decimal("0.00")) + commission_amount
            rc_obj.save(update_fields=["total_earnings"])
    except Exception:
        pass

    
    try:
        create_notification(
            user=referral.referrer,
            verb="referral_commission",
            title="Referral commission earned",
            message=f"You earned {commission_amount:.2f} as affiliate commission from a referred user's transaction.",
            data={"transaction_id": str(transaction.id), "amount": str(commission_amount)}
        )
    except Exception:
        pass

    return rc
