from django.urls import path
from .api_views import EnglishTestInfoView, StartTestView, SubmitAnswersView

urlpatterns = [
    path('english/', EnglishTestInfoView.as_view(), name='assessments-english-info'),
    path('tests/<uuid:test_id>/start/', StartTestView.as_view(), name='assessments-start'),
    path('tests/<uuid:test_id>/submit/', SubmitAnswersView.as_view(), name='assessments-submit'),
]
