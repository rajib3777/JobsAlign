from django.urls import path
from . import api_views

urlpatterns = [
    path('project/<uuid:project_id>/', api_views.ProjectRecommendationView.as_view(), name='project-recs'),
    path('project/<uuid:project_id>/trigger/', api_views.TriggerProjectRecommendation.as_view(), name='project-recs-trigger'),
    path('user/<uuid:user_id>/', api_views.UserRecommendationView.as_view(), name='user-recs'),
]
