from celery import shared_task
from .models import UserLevelProgress
from django.utils import timezone

@shared_task
def daily_streak_update():
    """
    Give XP to users who log in daily (engagement reward)
    """
    from accounts.models import CustomUser
    users = CustomUser.objects.filter(is_active=True)
    for u in users:
        prog, _ = UserLevelProgress.objects.get_or_create(user=u)
        prog.streak_days += 1
        prog.add_xp(10, reason="Daily Login Streak")
