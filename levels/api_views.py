# api_views.py
from rest_framework import generics, permissions
from .models import UserLevelProgress, UserAchievement
from .serializers import LevelProgressSerializer, UserAchievementSerializer

class MyLevelView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LevelProgressSerializer

    def get_object(self):
        progress, _ = UserLevelProgress.objects.get_or_create(user=self.request.user)
        return progress

class MyAchievementsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserAchievementSerializer

    def get_queryset(self):
        return UserAchievement.objects.filter(user=self.request.user)
