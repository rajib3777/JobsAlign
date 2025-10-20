from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

User = settings.AUTH_USER_MODEL

class Notification(models.Model):
    
    LEVELS = [('info','info'), ('success','success'), ('warning','warning'), ('critical','critical')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='actor_notifications')
    verb = models.CharField(max_length=120)  # short human readable action
    title = models.CharField(max_length=255)  # short headline
    message = models.TextField(blank=True, null=True)
    level = models.CharField(max_length=20, choices=LEVELS, default='info')
    data = models.JSONField(default=dict, blank=True, help_text="Related ids and metadata")
    read = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    group_key = models.CharField(max_length=255, blank=True, null=True, db_index=True)  # for dedupe/stacking
    is_push_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user','read']),
            models.Index(fields=['group_key','created_at']),
        ]

    def __str__(self):
        return f"{self.user} ← {self.verb} @ {self.created_at.isoformat()}"

class NotificationPreference(models.Model):
    """
    Per-user settings controlling channels and type-level opt-in/out.
    """
    CHANNELS = [('inapp','inapp'), ('email','email'), ('push','push')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_preferences')
    enabled = models.BooleanField(default=True)
    channel = models.CharField(max_length=20, choices=CHANNELS, default='inapp')
    notification_type = models.CharField(max_length=50, blank=True, null=True,
                                         help_text="If set, this preference applies to a specific notification type (verb)")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user','channel','notification_type')
