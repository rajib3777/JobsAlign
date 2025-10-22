from rest_framework import serializers
from .models import UserAnalytics, PlatformAnalytics, TrendForecast, JobMarketInsight

class UserAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnalytics
        fields = "__all__"

class PlatformAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformAnalytics
        fields = "__all__"

class ForecastSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrendForecast
        fields = "__all__"


class JobMarketInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobMarketInsight
        fields = "__all__"
