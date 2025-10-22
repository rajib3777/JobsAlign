from celery import shared_task
from .utils import compute_category_metrics_for_date
from django.utils import timezone
from .models import Category, CategoryMetric
from django.conf import settings

@shared_task(bind=True)
def daily_category_metrics(self):
    date = timezone.now().date()
    compute_category_metrics_for_date(date=date)

@shared_task(bind=True)
def compute_trending_scores(self, days=14):
    """
    Compute trending score per category: simple demand growth vs avg.
    """
    from django.db.models import Sum
    today = timezone.now().date()
    cats = Category.objects.filter(is_active=True)
    for cat in cats:
        past = CategoryMetric.objects.filter(category=cat, date__gte=(today - timezone.timedelta(days=days)))
        total_demand = past.aggregate(sum_d=Sum('demand'))['sum_d'] or 0
        avg = (total_demand / days) if days else 0
        latest = past.order_by('-date').first()
        latest_d = latest.demand if latest else 0
        trending = 0.0
        if avg > 0:
            trending = (latest_d - avg) / avg
        # clamp
        if trending > 3:
            trending = 3.0
        if trending < -1:
            trending = -1.0
        # write to latest metric
        if latest:
            latest.trending_score = trending
            latest.save(update_fields=['trending_score'])
