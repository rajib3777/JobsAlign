from rest_framework import generics, permissions
from .models import UserAnalytics, PlatformAnalytics, TrendForecast
from .serializers import UserAnalyticsSerializer, PlatformAnalyticsSerializer, ForecastSerializer
from accounts.models import User
from .utils import calculate_user_metrics
from .models import JobMarketInsight
from .serializers import JobMarketInsightSerializer
from rest_framework import generics, permissions

class MyAnalyticsView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserAnalyticsSerializer

    def get_object(self):
        user = self.request.user
        calculate_user_metrics(user)
        return UserAnalytics.objects.get(user=user)


class PlatformAnalyticsView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = PlatformAnalytics.objects.all().order_by("-date")[:30]
    serializer_class = PlatformAnalyticsSerializer


class ForecastView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = TrendForecast.objects.all().order_by("-generated_at")[:10]
    serializer_class = ForecastSerializer



class JobMarketInsightsView(generics.ListAPIView):
    queryset = JobMarketInsight.objects.all().order_by('-demand_score')
    serializer_class = JobMarketInsightSerializer
    permission_classes = [permissions.AllowAny]