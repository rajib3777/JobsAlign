from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/marketplace/", include("marketplace.urls")),
    path("api/chats/", include("chats.urls")),
    path("api/reviews/", include("reviews.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/categories/", include("categories.urls")),
    path("api/disputes/", include("disputes.urls")),
    path("api/levels/", include("levels.urls")),
    path("api/subscriptions/", include("subscriptions.urls")),
    path("api/verification/", include("verification.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/recommendations/", include("recommendations.urls")),
    path("api/support/", include("support.urls")),
    path("api/referrals/", include("referrals.urls")),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('frontend/pages/login.html', TemplateView.as_view(template_name="pages/login.html")),
    path('frontend/pages/freelancer_dashboard.html', TemplateView.as_view(template_name="pages/freelancer_dashboard.html")),

]
