from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

User = settings.AUTH_USER_MODEL

VERIFICATION_STATUS = [
    ('pending','Pending'),
    ('under_review','Under Review'),
    ('approved_basic','Approved (Basic)'),
    ('approved_advanced','Approved (Advanced)'),
    ('rejected','Rejected'),
    ('expired','Expired'),
]

DOCUMENT_TYPES = [
    ('nid','National ID'),
    ('passport','Passport'),
    ('driver_license','Driver License'),
    ('company_doc','Company Document'),
    ('other','Other'),
]

def user_upload_path(instance, filename):
    return f"verification/{instance.user_id}/{instance.id}/{filename}"

class VerificationRequest(models.Model):
    """
    Represents a user's verification flow. A user can have multiple requests over time.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_requests')
    status = models.CharField(max_length=30, choices=VERIFICATION_STATUS, default='pending', db_index=True)
    tier = models.CharField(max_length=30, default='basic', help_text='basic|advanced|business')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    # decision metadata (auditable)
    decision_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='verification_decisions')
    decision_reason = models.TextField(blank=True, null=True)
    decision_at = models.DateTimeField(null=True, blank=True)
    meta = models.JSONField(default=dict, blank=True)  # e.g., {"ocr_score":0.9, "face_match":0.98}
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def mark_approved(self, tier='basic', actor=None, reason=None):
        self.status = 'approved_basic' if tier == 'basic' else 'approved_advanced'
        self.decision_by = actor
        self.decision_reason = reason
        self.decision_at = timezone.now()
        # set retention expiry
        retention_days = getattr(settings, 'VERIFICATION', {}).get('RETENTION_DAYS', 365)
        self.expires_at = timezone.now() + timezone.timedelta(days=retention_days)
        self.save(update_fields=['status','decision_by','decision_reason','decision_at','expires_at','updated_at'])

    def mark_rejected(self, actor=None, reason=None):
        self.status = 'rejected'
        self.decision_by = actor
        self.decision_reason = reason
        self.decision_at = timezone.now()
        self.save(update_fields=['status','decision_by','decision_reason','decision_at','updated_at'])

    def mark_under_review(self):
        self.status = 'under_review'
        self.save(update_fields=['status','updated_at'])

    def __str__(self):
        return f"VerificationRequest {self.id} - {self.user}"


class Document(models.Model):
    """
    User uploaded document (front/back or company doc).
    Files should be stored in secure storage and virus-scanned.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(VerificationRequest, on_delete=models.CASCADE, related_name='documents')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to=user_upload_path)
    filename = models.CharField(max_length=255, blank=True)
    filesize = models.BigIntegerField(null=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    processed = models.BooleanField(default=False)
    meta = models.JSONField(default=dict, blank=True)  # OCR outputs, hashes, scan results
    redacted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-uploaded_at']

    def save(self, *args, **kwargs):
        if not self.filename and self.file:
            self.filename = getattr(self.file, 'name', '') or ''
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Document {self.filename} for {self.user}"


class Selfie(models.Model):
    """
    Selfie image uploaded by user for face match.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(VerificationRequest, on_delete=models.CASCADE, related_name='selfies')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_selfies')
    file = models.FileField(upload_to=user_upload_path)
    uploaded_at = models.DateTimeField(default=timezone.now)
    processed = models.BooleanField(default=False)
    meta = models.JSONField(default=dict, blank=True)  # face-match score etc.

    def __str__(self):
        return f"Selfie {self.id} for {self.user}"


class VerificationAudit(models.Model):
    """
    Immutable audit trail entries for every action on a verification request.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(VerificationRequest, on_delete=models.CASCADE, related_name='audits')
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    verb = models.CharField(max_length=120)  # e.g., 'submitted_document', 'ocr_processed', 'approved'
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Audit {self.verb} @ {self.request.id}"
