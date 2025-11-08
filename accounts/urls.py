from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .api_views import (
    RegisterView, UserProfileView, GoogleLoginView, LogoutView,
    PasswordChangeView, PasswordResetConfirmView, PasswordResetRequestView,VerifyEmailView
    ,KYCUploadView,ProfileUpdateView
)
from .import views

urlpatterns = [

    path("login-page/", views.login_page, name="login_page"),
    path("register-page/", views.register_page, name="register_page"),

    
    # 🔹 User Registration and Profile
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-email/<uidb64>/<token>/", VerifyEmailView.as_view(), name="verify-email"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),

    # 🔹 JWT Token Authentication
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),

    #🔹 Password Reset and Change
    path("password/change/", PasswordChangeView.as_view(), name="password_change"),
    path("password/reset/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("password/reset/confirm/<uidb64>/<token>/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),

    #🔹 Google Authentication
    path("google/login/", GoogleLoginView.as_view(), name="google_login"),
    path("kyc/upload/", KYCUploadView.as_view(), name="kyc_upload"),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile-update'),

    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
