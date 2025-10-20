from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

User = settings.AUTH_USER_MODEL

class ProjectRecommendation(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_id = models.UUIDField(db_index=True)  # marketplace.Project.id
    computed_at = models.DateTimeField(default=timezone.now, db_index=True)
    payload = models.JSONField(default=list, help_text="List of {user_id, score, reason}")  # ordered descending
    source = models.CharField(max_length=50, default="heuristic")  # 'heuristic' or 'ml'
    ttl_seconds = models.IntegerField(default=3600)  # cache TTL

    class Meta:
        indexes = [
            models.Index(fields=['project_id','computed_at']),
        ]

    def __str__(self):
        return f"Recommendations for {self.project_id} @ {self.computed_at.isoformat()}"

class UserRecommendation(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    computed_at = models.DateTimeField(default=timezone.now, db_index=True)
    payload = models.JSONField(default=list, help_text="List of {project_id, score, reason}")
    source = models.CharField(max_length=50, default="heuristic")
    ttl_seconds = models.IntegerField(default=3600)

    class Meta:
        indexes = [
            models.Index(fields=['user','computed_at']),
        ]

    def __str__(self):
        return f"Recommendations for {self.user_id} @ {self.computed_at.isoformat()}"

