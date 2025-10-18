from celery import shared_task
from decimal import Decimal
from .models import Bid, Project

@shared_task
def compute_suggested_bid(project_id):
    """
    Dummy AI task to compute a suggested bid range for a project.
    In production, this can call an external ML API.
    """
    try:
        project = Project.objects.get(id=project_id)
        avg_budget = (project.budget_min + project.budget_max) / 2

        # Example “AI” logic (later replace with real model)
        suggestion = {
            "suggested_price": str(round(avg_budget * Decimal("0.9"), 2)),
            "confidence": 0.82,
            "comment": "Suggested bid based on similar project patterns."
        }

        # Update all pending bids
        for bid in project.bids.filter(status="pending"):
            bid.suggested_by_ai = suggestion
            bid.save(update_fields=["suggested_by_ai"])
        return True
    except Project.DoesNotExist:
        return False
