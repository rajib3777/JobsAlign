from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
from decimal import Decimal

User = settings.AUTH_USER_MODEL

REFERRAL_STATUS = [
    ("pending", "Pending"),
    ("completed", "Completed"),
    ("fraud", "Fraud Detected"),
    ("expired", "Expired"),
]

REWARD_TYPE = [
    ("wallet", "Wallet Credit"),
    ("xp", "XP Points"),
    ("discount", "Subscription Discount"),
]

class ReferralCode(models.Model):
    """
    One referral code per user. Unique short code.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="referral_code")
    code = models.CharField(max_length=20, unique=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    total_signups = models.PositiveIntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    def __str__(self):
        return f"{self.user} ({self.code})"


class Referral(models.Model):
    """
    A referral relationship: referrer -> referred (may be created before referred user exists).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="affiliate_referrals")
    referred = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="referred_by")
    code_used = models.CharField(max_length=20, db_index=True)
    status = models.CharField(max_length=20, choices=REFERRAL_STATUS, default="pending")
    reward_given = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_fingerprint = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    activated_at = models.DateTimeField(null=True, blank=True)
    total_commission = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        indexes = [models.Index(fields=["code_used"]), models.Index(fields=["referrer"])]

    def __str__(self):
        return f"{self.referrer} → {self.referred or 'Pending'} ({self.code_used})"


class ReferralCommission(models.Model):
    """
    A commission record generated from a transaction by a referred user.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name="commissions")
    transaction_id = models.CharField(max_length=128, db_index=True)
    base_amount = models.DecimalField(max_digits=14, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("2.00"))  # percent
    earned_amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    paid = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=["transaction_id"]), models.Index(fields=["created_at"])]

    def __str__(self):
        return f"Commission {self.earned_amount} for {self.referral.referrer}"
