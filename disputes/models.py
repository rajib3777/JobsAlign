from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

User = settings.AUTH_USER_MODEL

class Dispute(models.Model):
    STATUS_CHOICES = [
        ('open','Open'),
        ('under_review','Under Review'),
        ('mediation','Mediation'),
        ('escalated','Escalated'),
        ('resolved_buyer','Resolved (Buyer)'),
        ('resolved_freelancer','Resolved (Freelancer)'),
        ('cancelled','Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.OneToOneField('marketplace.Contract', on_delete=models.CASCADE, related_name='dispute')
    opener = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opened_disputes')
    reason = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='open', db_index=True)
    assigned_mediator = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='mediations')
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    sla_deadline = models.DateTimeField(null=True, blank=True, help_text="Auto-escalation deadline")
    meta = models.JSONField(default=dict, blank=True)  # store resolution proposals, amounts, etc.

    class Meta:
        indexes = [
            models.Index(fields=['status','created_at']),
            models.Index(fields=['contract']),
        ]

    def __str__(self):
        return f"Dispute {self.id} ({self.contract_id})"

class Evidence(models.Model):
    """
    Evidence attachments or text blocks submitted by a party.
    Files should be virus-scanned and possibly redacted before storing.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispute = models.ForeignKey(Dispute, on_delete=models.CASCADE, related_name='evidences')
    uploader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to='disputes/evidence/', null=True, blank=True)
    text = models.TextField(blank=True, null=True)  # transcript / note
    meta = models.JSONField(default=dict, blank=True)  # ex: { 'redacted': True, 'sha256': '...' }
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

class DisputeTimeline(models.Model):
    """
    Immutable timeline entries for auditability: logs every action with actor, verb, payload.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispute = models.ForeignKey(Dispute, on_delete=models.CASCADE, related_name='timeline')
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    verb = models.CharField(max_length=120)  # e.g., 'opened', 'evidence_uploaded', 'mediator_assigned', 'proposal_made'
    payload = models.JSONField(default=dict, blank=True)  # structured context
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['created_at']

class ArbitrationDecision(models.Model):
    """
    Stores final decision object and (optionally) payout instructions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispute = models.OneToOneField(Dispute, on_delete=models.CASCADE, related_name='decision')
    decided_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='decisions')
    decided_at = models.DateTimeField(default=timezone.now)
    decision = models.CharField(max_length=50)  # e.g., 'buyer_wins', 'freelancer_wins', 'split'
    details = models.JSONField(default=dict, blank=True)  # payout amounts, refunds, commission, notes

