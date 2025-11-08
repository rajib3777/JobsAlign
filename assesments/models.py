from django.db import models
from django.conf import settings
from django.utils import timezone
from categories.models import SubCategory, Skill
import uuid

User = settings.AUTH_USER_MODEL

class Test(models.Model):
    TEST_TYPES = [('english', 'Basic English'), ('skill', 'Skill Based')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=TEST_TYPES)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, null=True, blank=True, related_name='tests')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, null=True, blank=True, related_name='tests')
    total_marks = models.PositiveIntegerField(default=100)
    pass_marks = models.PositiveIntegerField(default=60)
    weight = models.FloatField(default=5.0)  # english=5.0, skill=10.0
    time_limit_sec = models.PositiveIntegerField(default=1200)  # 20 mins
    randomize = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    max_attempts = models.PositiveIntegerField(default=3)  # <= 3 attempts per user

    class Meta:
        indexes = [models.Index(fields=['type','active'])]

    def __str__(self):
        return f"{self.name} [{self.get_type_display()}]"


class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    options = models.JSONField(help_text="{'A':'...','B':'...','C':'...','D':'...'}")
    correct_answer = models.CharField(max_length=5)

    def __str__(self):
        return f"{self.text[:60]}..."


class Attempt(models.Model):
    STATUS = [('started','Started'),('submitted','Submitted'),('graded','Graded'),('invalid','Invalid')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="test_attempts")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="attempts")
    attempt_no = models.PositiveIntegerField(default=1)  # 1..max_attempts
    status = models.CharField(max_length=10, choices=STATUS, default='started')
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_sec = models.PositiveIntegerField(default=0)
    score = models.FloatField(default=0.0)
    percent_cached = models.FloatField(default=0.0)  # contribution to profile %
    passed = models.BooleanField(default=False)
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('user','test','attempt_no')]  # same attempt_no can't duplicate
        indexes = [models.Index(fields=['user','test'])]

    def mark_invalid(self, reason="time_limit_exceeded"):
        self.status = 'invalid'
        self.meta['invalid_reason'] = reason
        self.save(update_fields=['status','meta'])


class Answer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    chosen = models.CharField(max_length=5)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = [('attempt','question')]
