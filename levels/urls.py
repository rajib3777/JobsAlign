# urls.py
from django.urls import path
from . import api_views

urlpatterns = [
    path("me/", api_views.MyLevelView.as_view(), name="my-level"),
    path("me/achievements/", api_views.MyAchievementsView.as_view(), name="my-achievements"),
]
