from django.urls import path
from . import api_views as views


urlpatterns = [

    path("projects/", views.ProjectCreateView.as_view(), name="project-create"),
    path("projects/<uuid:pk>/", views.ProjectRetrieveUpdateView.as_view(), name="project-detail"),
    path("projects/<uuid:project_id>/bids/", views.BidListView.as_view(), name="project-bids"),
    path("bids/create/", views.BidCreateView.as_view(), name="bid-create"),
    path("bids/<uuid:bid_id>/accept/", views.AcceptBidView.as_view(), name="bid-accept"),
    path("contracts/<uuid:pk>/", views.ContractDetailView.as_view(), name="contract-detail"),
    path("milestones/create/", views.MilestoneCreateView.as_view(), name="milestone-create"),
    path("milestones/<uuid:milestone_id>/approve/", views.MilestoneApproveView.as_view(), name="milestone-approve"),
]
