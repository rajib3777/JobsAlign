from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),

    # 🔹 All API apps
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

    # 🔹 Frontend pages
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('login/', TemplateView.as_view(template_name="login.html"), name='login_page'),
    path('register/', TemplateView.as_view(template_name="register.html"), name='register_page'),

    # ✅ Frontend (Freelancer)
    # Freelancer portal
    path("frontend/pages/freelancer_dashboard.html", 
     TemplateView.as_view(template_name="freelancer_dashboard.html")),
    path("freelancer/profile/", TemplateView.as_view(template_name="pages/freelancer_profile.html"), name="freelancer_profile"),
    path("freelancer/jobs/", TemplateView.as_view(template_name="pages/jobs.html"), name="freelancer_jobs"),
    path("freelancer/chat/", TemplateView.as_view(template_name="pages/chat.html"), name="freelancer_chat"),
    path("freelancer/payments/", TemplateView.as_view(template_name="pages/payments.html"), name="freelancer_payments"),
    path("freelancer/reviews/", TemplateView.as_view(template_name="pages/reviews.html"), name="freelancer_reviews"),
    path("freelancer/analytics/", TemplateView.as_view(template_name="pages/analytics.html"), name="freelancer_analytics"),
    path("freelancer/verification/", TemplateView.as_view(template_name="pages/verification.html"), name="freelancer_verification"),
    path("freelancer/support/", TemplateView.as_view(template_name="pages/support.html"), name="freelancer_support"),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
