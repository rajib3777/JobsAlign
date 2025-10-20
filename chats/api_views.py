from rest_framework import generics, status, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone

from .models import Conversation, Participant, Message, MessageReceipt, MessageThread
from .serializers import (
    ConversationSerializer, ConversationCreateSerializer,
    ParticipantSerializer, MessageSerializer, MessageCreateSerializer, ThreadSerializer
)
from .permissions import IsConversationParticipant
from . import utils

class ConversationCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationCreateSerializer

    def perform_create(self, serializer):
        conv = serializer.save()
        return conv

class ConversationDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsConversationParticipant]
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer

class AddParticipantView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ParticipantSerializer

    def post(self, request, conversation_id):
        conv = get_object_or_404(Conversation, id=conversation_id)
        if not conv.participants.filter(user=request.user).exists():
            return Response({'detail':'Forbidden'}, status=403)
        user_id = request.data.get('user_id')
        User = __import__('django.contrib.auth').contrib.auth.get_user_model()
        user = get_object_or_404(User, id=user_id)
        participant, created = Participant.objects.get_or_create(conversation=conv, user=user)
        return Response(ParticipantSerializer(participant).data, status=201 if created else 200)

class MessageCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsConversationParticipant]
    serializer_class = MessageCreateSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        msg = serializer.save()
        # create receipts
        participants = msg.conversation.participants.exclude(user=msg.sender)
        receipts = [MessageReceipt(message=msg, user=p.user) for p in participants]
        MessageReceipt.objects.bulk_create(receipts, ignore_conflicts=True)
        # notify channel layer & background jobs
        utils.notify_message_created(msg)
        return msg

class MessageListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsConversationParticipant]
    serializer_class = MessageSerializer
    pagination_class = None

    def get_queryset(self):
        conv_id = self.kwargs.get('conversation_id')
        conv = get_object_or_404(Conversation, id=conv_id)
        qs = conv.messages.select_related('sender').all().order_by('created_at')
        # optional: support cursor pagination or limit param
        limit = int(self.request.query_params.get('limit', 50))
        offset = int(self.request.query_params.get('offset', 0))
        return qs[offset:offset+limit]

class MarkAsReadView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsConversationParticipant]

    def post(self, request, conversation_id):
        conv = get_object_or_404(Conversation, id=conversation_id)
        p = conv.participants.get(user=request.user)
        p.last_read_at = timezone.now()
        p.save(update_fields=['last_read_at'])
        MessageReceipt.objects.filter(message__conversation=conv, user=request.user, read_at__isnull=True).update(read_at=timezone.now())
        return Response({'detail':'ok'})

class ThreadCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsConversationParticipant]
    serializer_class = ThreadSerializer

    def perform_create(self, serializer):
        thread = serializer.save(created_by=self.request.user)
        return thread

# Actions: react/edit/pin via simple endpoints
from rest_framework.decorators import api_view, permission_classes
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsConversationParticipant])
def react_message(request, message_id):
    emoji = request.data.get('emoji')
    if not emoji:
        return Response({'detail':'emoji required'}, status=400)
    msg = get_object_or_404(Message, id=message_id)
    if not msg.conversation.participants.filter(user=request.user).exists():
        return Response({'detail':'Forbidden'}, status=403)
    user_id = str(request.user.id)
    # toggle reaction
    reactions = msg.reactions or {}
    users = reactions.get(emoji, [])
    if user_id in users:
        users.remove(user_id)
    else:
        users.append(user_id)
    reactions[emoji] = users
    msg.reactions = reactions
    msg.save(update_fields=['reactions'])
    utils.notify_reaction_updated(msg, emoji, request.user)
    return Response({'detail':'ok'})

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsConversationParticipant])
def edit_message(request, message_id):
    content = request.data.get('content', '')
    msg = get_object_or_404(Message, id=message_id)
    if request.user != msg.sender:
        return Response({'detail':'Forbidden'}, status=403)
    # store edit log
    prev = {'content': msg.content, 'edited_at': str(msg.edited_at), 'editor': str(request.user.id)}
    msg.edit_log = (msg.edit_log or []) + [prev]
    msg.content = content
    msg.edited_at = timezone.now()
    msg.save(update_fields=['content','edited_at','edit_log'])
    utils.notify_message_edited(msg)
    return Response({'detail':'ok'})

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsConversationParticipant])
def pin_message(request, message_id):
    msg = get_object_or_404(Message, id=message_id)
    conv = msg.conversation
    # only participants can pin; optionally require is_admin
    if not conv.participants.filter(user=request.user).exists():
        return Response({'detail':'Forbidden'}, status=403)
    msg.pinned = bool(request.data.get('pinned', True))
    msg.save(update_fields=['pinned'])
    utils.notify_message_pinned(msg)
    return Response({'detail':'ok'})
