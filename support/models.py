from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

User = settings.AUTH_USER_MODEL

TICKET_STATUS = [
    ('open','Open'),
    ('pending_agent','Pending (Agent)'),
    ('pending_user','Pending (User)'),
    ('escalated','Escalated'),
    ('resolved','Resolved'),
    ('closed','Closed'),
]

PRIORITY = [
    ('low','Low'),
    ('medium','Medium'),
    ('high','High'),
    ('urgent','Urgent'),
]

class TicketCategory(models.Model):
    """
    e.g. Billing, Payment, Dispute, Technical, Verification
    Only admin can create categories.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class SupportTicket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=255)
    category = models.ForeignKey(TicketCategory, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=30, choices=TICKET_STATUS, default='open', db_index=True)
    priority = models.CharField(max_length=20, choices=PRIORITY, default='medium')
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_tickets')  # agent
    is_internal = models.BooleanField(default=False, help_text="Internal note only")
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-updated_at']

    def mark_resolved(self, actor=None, note=None):
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save(update_fields=['status','resolved_at','updated_at'])
        from .models import TicketMessage
        TicketMessage.objects.create(ticket=self, sender=actor, content=(note or "Marked resolved by agent"), internal=False, system=True)

    def __str__(self):
        return f"{self.subject} ({self.id})"


class TicketMessage(models.Model):
    """
    Messages inside a ticket. sender=None for system messages.
    internal flag: only agents/admins can view.
    system flag: system-generated
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='support_messages')
    content = models.TextField()
    internal = models.BooleanField(default=False)
    system = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    attachments = models.JSONField(default=list, blank=True)  # list of URLs/metadata

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Msg {self.id} on {self.ticket.id}"


class CannedResponse(models.Model):
    """
    Predefined agent replies for faster response.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class SupportAudit(models.Model):
    """
    Immutable audit trail for each action.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='audits')
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    verb = models.CharField(max_length=120)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Audit {self.verb} for {self.ticket.id}"
