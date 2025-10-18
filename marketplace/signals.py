from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps

from .models import Project, Bid, Contract

@receiver(post_save, sender=Project)
def project_created(sender, instance, created, **kwargs):
    if created:
        # optional: enqueue AI matching job
        try:
            from .tasks import compute_project_matches
            compute_project_matches.delay(str(instance.id))
        except Exception:
            pass

@receiver(post_save, sender=Bid)
def bid_created(sender, instance, created, **kwargs):
    if created:
        # notify owner or log
        try:
            from .utils import log_activity
            log_activity(instance.project, instance.freelancer, "bid_created", {"bid_id":str(instance.id)})
        except Exception:
            pass
