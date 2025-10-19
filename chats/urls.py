from django.urls import path
from . import api_views

urlpatterns = [
    path("conversations/", api_views.ConversationListCreateView.as_view(), name="conversations-list-create"),
    path("conversations/<uuid:pk>/", api_views.ConversationDetailView.as_view(), name="conversations-detail"),
    path("conversations/<uuid:conversation_id>/messages/", api_views.MessageListCreateView.as_view(), name="conversation-messages"),
]
