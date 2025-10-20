from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Review
from .utils import update_user_rating

@receiver(post_save, sender=Review)
def update_rating_on_create(sender, instance, created, **kwargs):
    if created:
        update_user_rating(instance.reviewee)
