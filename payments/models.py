from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid

User = settings.AUTH_USER_MODEL

class Wallet(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="user_wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=10, default="BDT")
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} Wallet"

    def deposit(self, amount):
        self.balance += amount
        self.total_earned += amount
        self.save(update_fields=["balance", "total_earned", "updated_at"])

    def withdraw(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            self.total_spent += amount
            self.save(update_fields=["balance", "total_spent", "updated_at"])
            return True
        return False


class PaymentGateway(models.Model):
    name = models.CharField(max_length=50, unique=True)
    active = models.BooleanField(default=True)
    sandbox = models.BooleanField(default=True)
    credentials = models.JSONField(default=dict, help_text="API keys, secrets")

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TYPE_CHOICES = [
        ("deposit", "Deposit"),
        ("withdraw", "Withdraw"),
        ("escrow_hold", "Escrow Hold"),
        ("escrow_release", "Escrow Release"),
        ("refund", "Refund"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("reversed", "Reversed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    reference = models.CharField(max_length=255, blank=True, null=True, unique=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.type} ({self.amount})"

    def mark_success(self):
        self.status = "success"
        self.save(update_fields=["status", "updated_at"])

    def mark_failed(self, reason=None):
        self.status = "failed"
        if reason:
            self.remarks = reason
        self.save(update_fields=["status", "remarks", "updated_at"])


class Escrow(models.Model):
    job_id = models.CharField(max_length=255)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="escrow_buyer")
    freelancer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="escrow_freelancer")
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    commission = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    is_released = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    released_at = models.DateTimeField(blank=True, null=True)

    def release_payment(self):
        if not self.is_released:
            payout = self.amount - self.commission
            self.freelancer.wallet.deposit(payout)
            self.is_released = True
            self.released_at = timezone.now()
            self.save()


