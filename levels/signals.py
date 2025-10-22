from django.db.models.signals import post_save
from django.dispatch import receiver
from marketplace.models import Contract
from reviews.models import Review
from disputes.models import Dispute
from analytics.models import UserAnalytics
from .models import UserLevelProgress, Achievement, UserAchievement
from django.utils import timezone


@receiver(post_save, sender=Contract)
def on_contract_completed(sender, instance, **kwargs):
    if instance.status == 'completed':
        progress, _ = UserLevelProgress.objects.get_or_create(user=instance.freelancer)
        progress.add_xp(100, reason="Project Completed")

@receiver(post_save, sender=Review)
def on_positive_review(sender, instance, created, **kwargs):
    if created and instance.rating >= 4:
        progress, _ = UserLevelProgress.objects.get_or_create(user=instance.reviewee)
        progress.add_xp(50, reason="Positive Review")

@receiver(post_save, sender=Dispute)
def on_dispute_resolved(sender, instance, **kwargs):
    if instance.status in ('resolved_buyer', 'resolved_freelancer'):
        winner = instance.contract.freelancer if instance.status == 'resolved_freelancer' else instance.contract.buyer
        loser = instance.contract.buyer if instance.status == 'resolved_freelancer' else instance.contract.freelancer
        w_prog, _ = UserLevelProgress.objects.get_or_create(user=winner)
        w_prog.add_xp(40, reason="Dispute Resolved in Favor")
        l_prog, _ = UserLevelProgress.objects.get_or_create(user=loser)
        l_prog.add_xp(-80, reason="Dispute Lost")

@receiver(post_save, sender=UserAnalytics)
def on_growth_milestone(sender, instance, **kwargs):
    if instance.total_projects >= 50:
        ach = Achievement.objects.filter(title="50 Projects Club").first()
        if ach:
            UserAchievement.objects.get_or_create(user=instance.user, achievement=ach)
            progress, _ = UserLevelProgress.objects.get_or_create(user=instance.user)
            progress.add_xp(200, reason="50 Projects Milestone")
