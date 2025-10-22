from celery import shared_task
from .utils import calculate_user_metrics, aggregate_platform_metrics
from .models import TrendForecast
from django.utils import timezone
from accounts.models import User
import random

@shared_task
def daily_user_analytics():
    users = User.objects.all()
    for u in users:
        try:
            calculate_user_metrics(u)
        except Exception as e:
            print(f"[Analytics] Failed user metrics for {u.id}: {e}")

@shared_task
def daily_platform_analytics():
    try:
        aggregate_platform_metrics()
    except Exception as e:
        print(f"[Analytics] Platform aggregation failed: {e}")

@shared_task
def generate_ai_forecast():
    """
    Mock AI forecast (replace with ML model later)
    """
    metrics = ["revenue", "disputes", "signups", "reviews"]
    for m in metrics:
        TrendForecast.objects.create(
            period="weekly",
            metric=m,
            predicted_value=random.uniform(0.8, 1.2) * 100,
            confidence=random.uniform(80, 99),
        )



@shared_task
def update_job_market_insights():
    from .utils import generate_job_market_insights
    try:
        result = generate_job_market_insights()
        print(f"[Analytics] Updated market insights for {len(result)} categories")
    except Exception as e:
        print(f"[Analytics] Job market insights failed: {e}")
