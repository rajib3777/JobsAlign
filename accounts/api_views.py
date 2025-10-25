from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.generics import UpdateAPIView
from django.urls import reverse
from django.shortcuts import redirect
# Google Login dependencies
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView

from .models import User
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer, ChangePasswordSerializer
)
from .permissions import IsOwnerOrAdmin


# ✅ Custom JWT Token View (kept simple)
class CustomTokenObtainPairView(TokenObtainPairView):
    """Default view - override serializer_class if customizing claims."""
    pass


# ✅ Registration View
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


# ✅ Login View
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user, context={'request': request}).data
        }
        return Response(data, status=status.HTTP_200_OK)


# ✅ Logout View
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({"detail": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logged out"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


# ✅ User Profile View (Retrieve + Update)
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_object(self):
        # used get_object_or_404 just to make use of it logically
        return get_object_or_404(User, pk=self.request.user.pk)


# ✅ User List View (Admin only)
class UserListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = UserSerializer
    queryset = User.objects.all().order_by('-date_joined')


# ✅ Google Login View
class GoogleLoginView(SocialLoginView):
    """
    Google OAuth2 Login API
    Accepts access_token from frontend and logs in or creates the user.
    """
    adapter_class = GoogleOAuth2Adapter
    permission_classes = [AllowAny]


# ✅ Password Change View (using serializer to utilize ChangePasswordSerializer)
class PasswordChangeView(UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        old_password = serializer.validated_data.get("old_password")
        new_password = serializer.validated_data.get("new_password")

        # Verify old password
        if not user.check_password(old_password):
            return Response({"detail": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate new password
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({"detail": list(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Set and save new password
        user.set_password(new_password)
        user.save()

        return Response({"detail": "Password changed successfully!"}, status=status.HTTP_200_OK)


# ✅ Password Reset Request View
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Enter your Email!"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "There is no account using this email!"}, status=status.HTTP_404_NOT_FOUND)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = request.build_absolute_uri(
            reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
)           

        send_mail(
            subject="Password Reset Request",
            message=f"To reset your password, click the following link: {reset_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return Response({"success": "Reset link sent to your email!"}, status=status.HTTP_200_OK)


# ✅ Password Reset Confirm View
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Unauthorized access!"}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Token is invalid or expired!"}, status=status.HTTP_400_BAD_REQUEST)

        new_password = request.data.get("new_password")
        if not new_password:
            return Response({"error": "Enter your new password!"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"success": "Password reset successfully!"}, status=status.HTTP_200_OK)
    
    
class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            user.is_verified = True
            user.is_active = True
            user.save()
            return redirect('/frontend/pages/login.html?verified=true')
        else:
            return Response({"detail": "Invalid or expired verification link."}, status=status.HTTP_400_BAD_REQUEST)


class KYCUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        file = request.FILES.get('identity_document')
        if not file:
            return Response({"error": "Document file is required"}, status=400)
        user.identity_document = file
        user.is_identity_verified = False  # Admin must verify manually
        user.save()
        return Response({"message": "KYC document uploaded. Pending verification."})
