from django.urls import path
from . import api_views

urlpatterns = [
    path('create/', api_views.CreateDisputeView.as_view(), name='dispute-create'),
    path('<uuid:pk>/', api_views.DisputeDetailView.as_view(), name='dispute-detail'),
    path('<uuid:dispute_id>/evidence/', api_views.UploadEvidenceView.as_view(), name='dispute-evidence'),
    path('<uuid:dispute_id>/respond/', api_views.PartyRespondView.as_view(), name='dispute-respond'),
    path('<uuid:dispute_id>/assign-mediator/', api_views.AssignMediatorView.as_view(), name='dispute-assign'),
    path('<uuid:dispute_id>/propose/', api_views.ProposeResolutionView.as_view(), name='dispute-propose'),
    path('<uuid:dispute_id>/admin-resolve/', api_views.AdminResolveView.as_view(), name='dispute-admin-resolve'),
]
