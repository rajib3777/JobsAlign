from django.urls import path
from . import api_views

urlpatterns = [
    path('categories/', api_views.TicketCategoryListPublicView.as_view(), name='support-categories'),
    path('categories/manage/', api_views.TicketCategoryListCreateView.as_view(), name='support-categories-manage'),
    path('tickets/create/', api_views.CreateTicketView.as_view(), name='support-ticket-create'),
    path('tickets/me/', api_views.MyTicketsListView.as_view(), name='support-my-tickets'),
    path('tickets/<uuid:pk>/', api_views.TicketDetailView.as_view(), name='support-ticket-detail'),
    path('tickets/<uuid:ticket_id>/assign/', api_views.AssignTicketView.as_view(), name='support-ticket-assign'),
    path('tickets/<uuid:ticket_id>/resolve/', api_views.ResolveTicketView.as_view(), name='support-ticket-resolve'),
    path('messages/post/', api_views.UserPostMessageView.as_view(), name='support-message-user-post'),
    path('messages/agent/post/', api_views.PostMessageView.as_view(), name='support-message-agent-post'),
    path('agent/pending/', api_views.AgentPendingTicketsView.as_view(), name='support-agent-pending'),
    path('canned/', api_views.CannedResponseListCreateView.as_view(), name='support-canned'),
]
