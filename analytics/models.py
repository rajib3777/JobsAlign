from django.db import models
from django.utils import timezone
from django.conf import settings
import uuid

User = settings.AUTH_USER_MODEL

class UserAnalytics(models.Model):
    """
    Aggregated metrics for each user (freelancer or buyer)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="analytics")

    # Basic stats
    total_projects = models.PositiveIntegerField(default=0)
    completed_projects = models.PositiveIntegerField(default=0)
    ongoing_projects = models.PositiveIntegerField(default=0)

    # Financial
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_project_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Ratings & trust
    average_rating = models.FloatField(default=0)
    dispute_rate = models.FloatField(default=0)
    on_time_delivery = models.FloatField(default=0)
    recommendation_score = models.FloatField(default=0)

    # AI metrics
    risk_score = models.FloatField(default=0)  # probability of dispute or fraud
    growth_index = models.FloatField(default=0)  # career growth potential
    trust_index = models.FloatField(default=0)  # composite trust value

    # Engagement
    messages_sent = models.PositiveIntegerField(default=0)
    notifications_read = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Analytics for {self.user}"


class PlatformAnalytics(models.Model):
    """
    Daily snapshot for the entire JobsAlign platform
    """
    date = models.DateField(default=timezone.now, unique=True)
    total_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    total_projects = models.PositiveIntegerField(default=0)
    total_disputes = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    avg_completion_time = models.FloatField(default=0)
    avg_rating = models.FloatField(default=0)
    trust_health = models.FloatField(default=0)
    ai_confidence = models.FloatField(default=0)  # accuracy of recommendation model
    system_load = models.FloatField(default=0)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Platform Analytics {self.date}"


class TrendForecast(models.Model):
    """
    AI-based prediction for next period performance.
    """
    period = models.CharField(max_length=50, help_text="e.g., weekly, monthly")
    metric = models.CharField(max_length=50, help_text="e.g., revenue, disputes, signups")
    predicted_value = models.FloatField()
    confidence = models.FloatField(default=0)
    generated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Forecast {self.metric} ({self.period})"
    

class JobMarketInsight(models.Model):
    """
    Predictive analytics for job market demand, freelancer competition,
    and success probability per skill/category.
    """
    category = models.CharField(max_length=100)
    skill = models.CharField(max_length=100, blank=True, null=True)
    demand_score = models.FloatField(default=0)  # how many buyers posting similar jobs
    competition_score = models.FloatField(default=0)  # how many freelancers bidding
    success_probability = models.FloatField(default=0)  # chance of project completion
    avg_bid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_hire_time = models.FloatField(default=0)  # in hours
    trend_direction = models.CharField(max_length=10, default="stable")  # up / down / stable
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.category} - {self.skill or 'General'}"

