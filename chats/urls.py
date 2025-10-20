from django.urls import path
from . import api_views

urlpatterns = [
    path('conversations/create/', api_views.ConversationCreateView.as_view(), name='conversation-create'),
    path('conversations/<uuid:pk>/', api_views.ConversationDetailView.as_view(), name='conversation-detail'),
    path('conversations/<uuid:conversation_id>/messages/', api_views.MessageListView.as_view(), name='message-list'),
    path('messages/create/', api_views.MessageCreateView.as_view(), name='message-create'),
    path('conversations/<uuid:conversation_id>/participants/add/', api_views.AddParticipantView.as_view(), name='participant-add'),
    path('conversations/<uuid:conversation_id>/mark-read/', api_views.MarkAsReadView.as_view(), name='mark-read'),
    path('threads/create/', api_views.ThreadCreateView.as_view(), name='thread-create'),
    path('messages/<uuid:message_id>/react/', api_views.react_message, name='react-message'),
    path('messages/<uuid:message_id>/edit/', api_views.edit_message, name='edit-message'),
    path('messages/<uuid:message_id>/pin/', api_views.pin_message, name='pin-message'),
]

