from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Conversation, Message
from .serializers import ConversationSerializer, ConversationCreateSerializer, MessageSerializer, MessageCreateSerializer
from .permissions import IsParticipant
from rest_framework.pagination import CursorPagination

class MessageCursorPagination(CursorPagination):
    page_size = 30
    ordering = "-created_at"

class ConversationListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).prefetch_related("participants").order_by("-updated_at")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ConversationCreateSerializer
        return ConversationSerializer

    def perform_create(self, serializer):
        conv = serializer.save()
        if self.request.user.id not in [u.id for u in conv.participants.all()]:
            conv.participants.add(self.request.user)

class ConversationDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, IsParticipant]
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer

class MessageListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsParticipant]
    pagination_class = MessageCursorPagination

    def get_queryset(self):
        conv_id = self.kwargs.get("conversation_id")
        conv = get_object_or_404(Conversation, id=conv_id)
        self.check_object_permissions(self.request, conv)
        return conv.messages.filter(is_deleted=False).order_by("-created_at")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MessageCreateSerializer
        return MessageSerializer

    def perform_create(self, serializer):
        msg = serializer.save()
        # bump conversation updated_at
        conv = msg.conversation
        conv.updated_at = msg.created_at
        conv.save(update_fields=["updated_at"])
        # broadcast helper (optional)
        from .utils import broadcast_message
        try:
            broadcast_message(msg)
        except Exception:
            pass
        return msg

