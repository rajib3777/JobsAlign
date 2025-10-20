from django.db.models import Avg
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Review
from accounts.models import User

def update_user_rating(user):
    """Recalculate user's average rating."""
    avg_score = Review.objects.filter(reviewee=user).aggregate(avg=Avg("rating"))["avg"] or 0
    user.rating = round(avg_score, 2)
    user.total_reviews = Review.objects.filter(reviewee=user).count()
    user.save(update_fields=["rating","total_reviews"])

def notify_review_created(review):
    """Notify via chat or websocket."""
    try:
        layer = get_channel_layer()
        message = {
            "type": "system.notification",
            "event": "review_created",
            "data": {
                "review_id": str(review.id),
                "reviewee": str(review.reviewee_id),
                "score": review.average_score,
                "comment": review.comment
            }
        }
        async_to_sync(layer.group_send)(f"user_{review.reviewee_id}", message)
    except Exception:
        pass
