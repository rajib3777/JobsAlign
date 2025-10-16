from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .api_views import (
    RegisterView, UserProfileView, GoogleLoginView, LogoutView,
    PasswordChangeView, PasswordResetRequestView, PasswordResetConfirmView,
)

urlpatterns = [
    # 🔹 User Registration and Profile
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),

    # 🔹 JWT Token Authentication
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),

    🔹 Password Reset and Change
    path("password/change/", PasswordChangeView.as_view(), name="password_change"),
    path("password/reset/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),

    🔹 Google Authentication
    path("google/login/", GoogleLoginView.as_view(), name="google_login"),
]
