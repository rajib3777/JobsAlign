from django.urls import path
from . import api_views

urlpatterns = [
    path('request/create/', api_views.CreateVerificationRequestView.as_view(), name='verification-create'),
    path('request/me/', api_views.MyVerificationRequestView.as_view(), name='verification-me'),
    path('upload/document/', api_views.UploadDocumentView.as_view(), name='verification-upload-document'),
    path('upload/selfie/', api_views.UploadSelfieView.as_view(), name='verification-upload-selfie'),
    path('admin/pending/', api_views.AdminListPendingView.as_view(), name='verification-admin-pending'),
    path('admin/decision/', api_views.AdminDecisionView.as_view(), name='verification-admin-decision'),
]
