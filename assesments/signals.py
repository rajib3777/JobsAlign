from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Attempt
from accounts.utils import calculate_profile_completion

@receiver(post_save, sender=Attempt)
def sync_profile_percent(sender, instance, **kwargs):
    if instance.status in ('graded','invalid'):
        calculate_profile_completion(instance.user)  # safe idempotent
