from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from django.contrib.postgres.fields import ArrayField  # keep if used elsewhere

User = settings.AUTH_USER_MODEL


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class Project(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_review", "In Review"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    category = models.ForeignKey(
    'categories.Category',
    null=True,
    blank=True,
    on_delete=models.SET_NULL,
    related_name='projects'
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    title = models.CharField(max_length=255)
    description = models.TextField()
    budget_min = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    budget_max = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    currency = models.CharField(max_length=10, default="BDT")
    skills = models.ManyToManyField(Skill, related_name="projects", blank=True)
    is_featured = models.BooleanField(default=False)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Smart fields — populated by background tasks or on-demand
    recommended_freelancers = models.JSONField(default=list, blank=True)  # list of user ids / metadata
    recommended_score = models.FloatField(default=0.0)  # matching score

    view_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.owner})"


class ProjectAttachment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="marketplace/projects/")
    name = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(default=timezone.now)


class Bid(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="bids")
    freelancer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_days = models.PositiveIntegerField(default=7)
    cover_letter = models.TextField(blank=True, null=True)
    suggested_by_ai = models.JSONField(default=dict, blank=True)  # e.g. suggested price, rationale
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("project", "freelancer")


class Contract(models.Model):
    """
    The accepted agreement between buyer (project.owner) and freelancer.
    When a contract is created we will create an escrow in payments app (via utils).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="contract")
    bid = models.OneToOneField(Bid, on_delete=models.SET_NULL, null=True, blank=True, related_name="contract")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contracts_as_buyer")
    freelancer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contracts_as_freelancer")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    commission = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(blank=True, null=True)
    # link to payments.Escrow via external id or OneToOne later
    escrow_reference = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Contract {self.id} ({self.project.title})"


class Milestone(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("submitted", "Submitted"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("paid", "Paid"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="milestones")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    submission_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.amount}"


class ProjectActivityLog(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="activity_logs")
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
