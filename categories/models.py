from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

User = settings.AUTH_USER_MODEL

VISIBILITY_CHOICES = [
    ('public','Public'),
    ('premium','Premium Only'),
    ('invite','Invite Only'),
]

class Category(models.Model):
    """
    Top-level category. Admin-created only.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='categories/icons/', null=True, blank=True)
    banner = models.ImageField(upload_to='categories/banners/', null=True, blank=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    premium_plan_slug = models.CharField(max_length=100, blank=True, null=True,
                                         help_text="If set, users need this subscription to access premium features in this category")
    manager = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='managed_categories')
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ('category','slug')
        ordering = ['name']

    def __str__(self):
        return f"{self.category.name} → {self.name}"


class Skill(models.Model):
    """
    Micro-skill or tag attached to subcategory and users/projects.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150)
    synonyms = models.JSONField(default=list, blank=True)  # alternate names
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('subcategory','slug')
        ordering = ['name']

    def __str__(self):
        return f"{self.subcategory.name} → {self.name}"


class FreelancerCategory(models.Model):
    """
    Which categories/subcategories a freelancer claims expertise in.
    Admin can approve (verified flag).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='freelancer_categories')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, null=True, blank=True, on_delete=models.SET_NULL)
    skills = models.ManyToManyField(Skill, blank=True)
    verified = models.BooleanField(default=False)
    verification_meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user','category','subcategory')

    def __str__(self):
        return f"{self.user} in {self.category.name}"


class CategoryMetric(models.Model):
    """
    Stores computed metrics for category/subcategory (demand, supply, avg_price, trending)
    updated by Celery.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='metrics')
    subcategory = models.ForeignKey(SubCategory, null=True, blank=True, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    demand = models.IntegerField(default=0)  # number of jobs posted
    supply = models.IntegerField(default=0)  # number of active freelancers
    avg_bid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_hire_time_hours = models.FloatField(default=0)
    success_rate = models.FloatField(default=0)  # % completed
    trending_score = models.FloatField(default=0)  # -1..1
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('category','subcategory','date')
        ordering = ['-date']

    def __str__(self):
        name = self.subcategory.name if self.subcategory else self.category.name
        return f"Metric: {name} @ {self.date}"


class CategoryNotificationPreference(models.Model):
    """
    Optional: per-user preference to receive new job alerts per category.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='category_prefs')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    notify_new_jobs = models.BooleanField(default=True)
    daily_digest = models.BooleanField(default=False)
    last_sent = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user','category')
