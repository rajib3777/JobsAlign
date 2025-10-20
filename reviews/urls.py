from django.urls import path
from . import api_views

urlpatterns = [
    path("create/", api_views.ReviewCreateView.as_view(), name="review-create"),
    path("user/<uuid:user_id>/", api_views.ReviewListView.as_view(), name="review-list"),
    path("<uuid:pk>/", api_views.ReviewDetailView.as_view(), name="review-detail"),
    path("<uuid:review_id>/reply/", api_views.ReviewReplyView.as_view(), name="review-reply"),
]
