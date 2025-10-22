from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

User = settings.AUTH_USER_MODEL

class Level(models.Model):
    """
    Static definitions of levels (thresholds, rewards)
    """
    name = models.CharField(max_length=50)
    xp_required = models.PositiveIntegerField()
    badge_icon = models.ImageField(upload_to='levels/icons/', blank=True, null=True)
    benefits = models.JSONField(default=dict, blank=True)  # e.g. {"boost": "profile_priority"}

    def __str__(self):
        return f"{self.name} (≥{self.xp_required} XP)"


class UserLevelProgress(models.Model):
    """
    Tracks XP and level per user.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="level_progress")
    xp = models.IntegerField(default=0)
    current_level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, blank=True)
    last_updated = models.DateTimeField(default=timezone.now)
    streak_days = models.PositiveIntegerField(default=0)

    def add_xp(self, amount, reason=None):
        self.xp += amount
        self.last_updated = timezone.now()
        self.save(update_fields=['xp', 'last_updated'])
        self.evaluate_level_up(reason)

    def evaluate_level_up(self, reason=None):
        new_level = Level.objects.filter(xp_required__lte=self.xp).order_by('-xp_required').first()
        if new_level and new_level != self.current_level:
            self.current_level = new_level
            self.save(update_fields=['current_level'])
            from notifications.utils import create_notification
            create_notification(
                user=self.user,
                verb='level_up',
                title=f'🎉 Level Up! You reached {new_level.name}',
                message=f"You gained XP from: {reason or 'activity'}",
                data={'level': new_level.name, 'xp': self.xp}
            )

    def __str__(self):
        return f"{self.user} - {self.current_level or 'No Level'} ({self.xp} XP)"


class Achievement(models.Model):
    """
    Special milestone rewards (e.g. '100 Projects Completed')
    """
    title = models.CharField(max_length=100)
    description = models.TextField()
    xp_reward = models.PositiveIntegerField(default=50)
    icon = models.ImageField(upload_to='levels/achievements/', blank=True, null=True)

    def __str__(self):
        return self.title


class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'achievement')
