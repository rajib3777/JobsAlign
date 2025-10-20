from django.db.models.signals import post_save
from django.dispatch import receiver
try:
    from marketplace.models import Project, Bid, Contract
    from . import tasks
except Exception:
    Project = None

# When a new project is created, schedule recalc
if Project is not None:
    @receiver(post_save, sender=Project)
    def on_project_saved(sender, instance, created, **kwargs):
        # schedule recompute asynchronously for new project
        try:
            tasks.compute_recommendations_for_project.delay(str(instance.id))
        except Exception:
            pass

    # When a contract is created/accepted, recompute recommendations for that project
    @receiver(post_save, sender=Contract)
    def on_contract_updated(sender, instance, created, **kwargs):
        # if contract created or status changed, recompute for the project
        try:
            tasks.compute_recommendations_for_project.delay(str(instance.project.id))
        except Exception:
            pass
