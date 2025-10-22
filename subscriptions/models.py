from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
from decimal import Decimal

User = settings.AUTH_USER_MODEL

class SubscriptionPlan(models.Model):
    """
    Plan definition (public). A plan may be recurring or one-time (but here we focus recurring).
    """
    BILLING_PERIODS = [('monthly','monthly'), ('annual','annual')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # price per period in platform currency
    currency = models.CharField(max_length=8, default=getattr(settings, 'DEFAULT_CURRENCY', 'USD'))
    billing_period = models.CharField(max_length=10, choices=BILLING_PERIODS, default='monthly')
    trial_days = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    priority_tier = models.PositiveIntegerField(default=0, help_text="Higher shows earlier in UI")
    feature_flags = models.JSONField(default=dict, blank=True, help_text="Map of entitlements & quotas")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority_tier','price']

    def __str__(self):
        return f"{self.name} ({self.billing_period}) - {self.price} {self.currency}"


class Coupon(models.Model):
    """
    Promotional coupons: percentage or fixed amount.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    percent_off = models.FloatField(null=True, blank=True)  # 0-100
    amount_off = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, default=getattr(settings, 'DEFAULT_CURRENCY', 'USD'))
    active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_redemptions = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def is_valid(self):
        if not self.active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        if self.max_redemptions and self.used_count >= self.max_redemptions:
            return False
        return True

    def apply_discount(self, amount: Decimal):
        if self.percent_off:
            return amount * (Decimal(1) - Decimal(self.percent_off)/Decimal(100))
        if self.amount_off:
            return max(Decimal(0), amount - Decimal(self.amount_off))
        return amount

    def __str__(self):
        return f"{self.code} - {'%s%%' % self.percent_off if self.percent_off else str(self.amount_off)}"


class UserSubscription(models.Model):
    """
    Active subscription for a user. Can represent team subscription (owner + seats) if needed.
    """
    STATUS = [
        ('active','active'),
        ('past_due','past_due'),
        ('cancelled','cancelled'),
        ('expired','expired'),
        ('trialing','trialing'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=STATUS, default='trialing')
    started_at = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    seats = models.PositiveIntegerField(default=1)
    proration_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    meta = models.JSONField(default=dict, blank=True)
    billing_customer_id = models.CharField(max_length=255, blank=True, null=True, help_text="Gateway customer id")
    last_payment_attempt = models.DateTimeField(null=True, blank=True)
    grace_period_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user','status']),
        ]

    def is_active(self):
        return self.status == 'active' or self.status == 'trialing'

    def __str__(self):
        return f"{self.user} -> {self.plan.name} ({self.status})"


class Invoice(models.Model):
    """
    Invoice record for billing/audit. One entry per charge.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='invoices')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default=getattr(settings, 'DEFAULT_CURRENCY', 'USD'))
    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    reference = models.CharField(max_length=255, blank=True, null=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_paid(self, reference=None, gateway_response=None):
        self.paid = True
        self.paid_at = timezone.now()
        if reference:
            self.reference = reference
        if gateway_response:
            self.gateway_response = gateway_response
        self.save(update_fields=['paid','paid_at','reference','gateway_response','updated_at'])


class BillingRecord(models.Model):
    """
    Detailed transaction log (not the gateway's transaction but internal billing).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='billing_records')
    invoice = models.ForeignKey(Invoice, null=True, blank=True, on_delete=models.SET_NULL)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default=getattr(settings, 'DEFAULT_CURRENCY', 'USD'))
    type = models.CharField(max_length=50, help_text="subscription_charge, refund, coupon_adjustment")
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

