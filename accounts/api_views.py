from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError

User = get_user_model()

# Google Login dependencies
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView

from .models import User
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer, ChangePasswordSerializer
)
from .permissions import IsOwnerOrAdmin

# If you want to customize token claims, create a custom TokenObtainPairSerializer
class CustomTokenObtainPairView(TokenObtainPairView):
    """Default view - override serializer_class if customizing claims."""
    pass


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


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


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # blacklisting requires token_blacklist app and storing the refresh token client-side
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({"detail": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logged out"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"detail": "Password updated."}, status=status.HTTP_200_OK)


class UserListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = UserSerializer
    queryset = User.objects.all().order_by('-date_joined')


# class GoogleLoginView(SocialLoginView):
#     """
#     Google OAuth2 Login API
#     Accepts access_token from frontend and logs in or creates the user.
#     """
#     adapter_class = GoogleOAuth2Adapter
#     permission_classes = [AllowAny]


#     class PasswordChangeView(APIView):
    
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         user = request.user
#         old_password = request.data.get("old_password")
#         new_password = request.data.get("new_password")

#         # Validate inputs
#         if not old_password or not new_password:
#             return Response(
#                 {"detail": "Both old_password and new_password are required."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # Check old password validity
#         if not user.check_password(old_password):
#             return Response(
#                 {"detail": "Old password is incorrect."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # Validate new password
#         try:
#             validate_password(new_password, user)
#         except ValidationError as e:
#             return Response({"detail": list(e)}, status=status.HTTP_400_BAD_REQUEST)

#         # Set new password
#         user.set_password(new_password)
#         user.save()

#         return Response({"detail": "Password changed successfully!"}, status=status.HTTP_200_OK)
