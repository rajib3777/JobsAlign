from django.utils import timezone
from accounts.models import UserProfile
from marketplace.models import Contract
from payments.models import Transaction
from reviews.models import Review
from disputes.models import Dispute
from notifications.models import Notification
from recommendations.models import Recommendation
from .models import UserAnalytics, PlatformAnalytics
from django.db.models import Avg, Sum, Count
from marketplace.models import Project, Bid
from django.db.models import Count, Avg, F
from .models import JobMarketInsight



def calculate_user_metrics(user):
    """
    Aggregate analytics for a specific user.
    """
    analytics, _ = UserAnalytics.objects.get_or_create(user=user)

    # Contracts
    contracts = Contract.objects.filter(
        freelancer=user
    ) if user.role == "freelancer" else Contract.objects.filter(buyer=user)
    
    analytics.total_projects = contracts.count()
    analytics.completed_projects = contracts.filter(status="completed").count()
    analytics.ongoing_projects = contracts.filter(status="active").count()

    # Payments
    tx = Transaction.objects.filter(user=user)
    analytics.total_earned = tx.filter(type="credit").aggregate(s=Sum("amount"))["s"] or 0
    analytics.total_spent = tx.filter(type="debit").aggregate(s=Sum("amount"))["s"] or 0

    # Reviews
    reviews = Review.objects.filter(reviewee=user)
    analytics.average_rating = reviews.aggregate(r=Avg("rating"))["r"] or 0

    # Disputes
    total_disputes = Dispute.objects.filter(contract__freelancer=user).count() + Dispute.objects.filter(contract__buyer=user).count()
    analytics.dispute_rate = (total_disputes / max(1, analytics.total_projects)) * 100

    # AI trust index
    analytics.trust_index = round(
        (analytics.average_rating * 0.6 + (100 - analytics.dispute_rate) * 0.4) / 10, 2
    )

    analytics.updated_at = timezone.now()
    analytics.save()
    return analytics


def aggregate_platform_metrics():
    """
    Collect global metrics from all apps.
    """
    data = {}
    from accounts.models import CustomUser

    data["total_users"] = CustomUser.objects.count()
    data["active_users"] = CustomUser.objects.filter(is_active=True).count()
    data["total_projects"] = Contract.objects.count()
    data["total_disputes"] = Dispute.objects.count()
    data["total_revenue"] = Transaction.objects.filter(type="credit").aggregate(s=Sum("amount"))["s"] or 0
    data["avg_rating"] = Review.objects.aggregate(r=Avg("rating"))["r"] or 0
    data["trust_health"] = round((100 - (Dispute.objects.count() / max(1, Contract.objects.count())) * 100), 2)

    PlatformAnalytics.objects.update_or_create(
        date=timezone.now().date(),
        defaults=data
    )
    return data



def generate_job_market_insights():
    """
    Analyze marketplace data to detect demand, competition, and success rates.
    """
    categories = Project.objects.values_list('category', flat=True).distinct()
    insights = []

    for cat in categories:
        projects = Project.objects.filter(category=cat)
        total_jobs = projects.count()
        if total_jobs == 0:
            continue

        # Buyer Demand
        demand_score = total_jobs

        # Freelancer competition (avg bids)
        bids = Bid.objects.filter(project__in=projects)
        competition_score = bids.values('freelancer').distinct().count()

        # Success Probability (completed / posted)
        completed = projects.filter(status='completed').count()
        success_probability = (completed / total_jobs) * 100

        # Average bid amount
        avg_bid = bids.aggregate(avg=Avg('amount'))['avg'] or 0

        # Avg hire time
        avg_hire_time = projects.exclude(accepted_at=None).aggregate(avg=Avg(F('accepted_at') - F('created_at')))['avg'] or 0

        JobMarketInsight.objects.update_or_create(
            category=cat,
            defaults={
                "demand_score": demand_score,
                "competition_score": competition_score,
                "success_probability": round(success_probability, 2),
                "avg_bid_amount": avg_bid,
                "avg_hire_time": avg_hire_time.total_seconds() / 3600 if avg_hire_time else 0,
                "trend_direction": "up" if success_probability > 70 else "down" if success_probability < 40 else "stable",
                "updated_at": timezone.now(),
            },
        )
        insights.append(cat)
    return insights
