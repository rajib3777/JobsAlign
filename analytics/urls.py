from django.urls import path
from . import api_views

urlpatterns = [
    path("me/", api_views.MyAnalyticsView.as_view(), name="user-analytics"),
    path("platform/", api_views.PlatformAnalyticsView.as_view(), name="platform-analytics"),
    path("forecast/", api_views.ForecastView.as_view(), name="forecast"),
    path("market-insights/", api_views.JobMarketInsightsView.as_view(), name="job-market-insights"),

]
