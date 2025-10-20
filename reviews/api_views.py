from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Review, ReviewReply
from .serializers import ReviewSerializer, ReviewCreateSerializer, ReviewReplySerializer
from .permissions import IsReviewParticipant
from . import utils

class ReviewCreateView(generics.CreateAPIView):
    serializer_class = ReviewCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        review = serializer.save()
        utils.update_user_rating(review.reviewee)
        utils.notify_review_created(review)
        return review

class ReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        return Review.objects.filter(reviewee_id=user_id)

class ReviewDetailView(generics.RetrieveAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsReviewParticipant]

class ReviewReplyView(generics.CreateAPIView):
    serializer_class = ReviewReplySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        review_id = self.kwargs.get("review_id")
        review = get_object_or_404(Review, id=review_id)
        serializer.save(responder=self.request.user, review=review)
