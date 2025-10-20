from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid

User = settings.AUTH_USER_MODEL

class Review(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.OneToOneField("marketplace.Contract", on_delete=models.CASCADE, related_name="review")
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="given_reviews")
    reviewee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_reviews")
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0.00"))
    title = models.CharField(max_length=255, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    professionalism = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0.00"))
    communication = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0.00"))
    quality = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0.00"))
    recommended = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    edited = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review {self.id} by {self.reviewer} → {self.reviewee}"

    @property
    def average_score(self):
        values = [self.rating, self.professionalism, self.communication, self.quality]
        return round(sum(values) / len(values), 2)

class ReviewReply(models.Model):
    """Allows the reviewee to respond once."""
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name="reply")
    responder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="review_replies")
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
