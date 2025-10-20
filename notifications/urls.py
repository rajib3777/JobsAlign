from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.NotificationListView.as_view(), name='notification-list'),
    path('detail/<uuid:pk>/', api_views.NotificationDetailView.as_view(), name='notification-detail'),
    path('read/', api_views.MarkReadView.as_view(), name='notification-mark-read'),
    path('archive/', api_views.ArchiveView.as_view(), name='notification-archive'),
    path('create/', api_views.CreateNotificationAPI.as_view(), name='notification-create'),
    path('preferences/', api_views.PreferenceListCreateView.as_view(), name='notification-preferences'),
]
