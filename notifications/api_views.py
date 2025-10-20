from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationCreateSerializer, PreferenceSerializer
from . import utils

class NotificationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user, archived=False)
        return qs

class NotificationDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()

    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            self.permission_denied(self.request)
        return obj

class MarkReadView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ids = request.data.get('ids', [])
        Notification.objects.filter(user=request.user, id__in=ids).update(read=True)
        return Response({'status':'ok'}, status=status.HTTP_200_OK)

class ArchiveView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ids = request.data.get('ids', [])
        Notification.objects.filter(user=request.user, id__in=ids).update(archived=True)
        return Response({'status':'ok'}, status=status.HTTP_200_OK)

class CreateNotificationAPI(generics.GenericAPIView):
    """
    Optional REST helper for external services to create notifications via HTTP.
    Use internal utils.create_notification for faster/safe calls.
    """
    permission_classes = [permissions.IsAuthenticated]  # limit to internal services or system user
    serializer_class = NotificationCreateSerializer

    def post(self, request):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        notif = utils.create_notification_via_api(request.user, **data)
        return Response(NotificationSerializer(notif).data, status=status.HTTP_201_CREATED)

class PreferenceListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PreferenceSerializer

    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

