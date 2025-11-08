from django.db.models.signals import post_save
from django.dispatch import receiver
from marketplace.models import Project
from .models import Category, FreelancerCategory
from notifications.utils import create_notification
from recommendations.tasks import compute_recommendations_for_project
from django.utils import timezone
from .utils import suggest_category_for_text
from .models import SubCategory

@receiver(post_save, sender=Project)
def on_project_created(sender, instance, created, **kwargs):
    if not created:
        return
    # 1) If project has no category, try to auto-suggest
    try:
        if not instance.category:
            suggestion = suggest_category_for_text(instance.title + " " + (instance.description or ""))
            if suggestion:
                # set suggested category slug in meta for admin review (do not auto-assign if policy requires admin)
                instance.meta = {**(instance.meta or {}), 'category_suggested': suggestion}
                instance.save(update_fields=['meta'])
    except Exception:
        pass

    # 2) Notify freelancers who opted in for that category (throttle inside notification util)
    try:
        cat = instance.category
        if cat:
            # get users who subscribed to notifications
            from categories.models import CategoryNotificationPreference
            prefs = CategoryNotificationPreference.objects.filter(category=cat, notify_new_jobs=True)
            for p in prefs:
                try:
                    create_notification(user=p.user, verb='new_job_in_category', title=f"New job in {cat.name}", message=instance.title, data={'project_id': str(instance.id), 'category': cat.slug})
                except Exception:
                    continue
    except Exception:
        pass

    # 3) Trigger recommendation compute for project
    try:
        compute_recommendations_for_project.delay(str(instance.id))
    except Exception:
        pass



@receiver(post_save, sender=SubCategory)
def notify_new_test(sender, instance, created, **kwargs):
    if created and instance.has_test:
        
        pass