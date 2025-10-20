import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Conversation, Participant, Message, MessageReceipt
from .serializers import MessageSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.group_name = f'chat_{self.conversation_id}'
        # verify participant
        is_participant = await self._is_participant()
        if not is_participant:
            await self.close()
            return
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        # presence: mark as online in Redis
        await self.accept()
        await self.channel_layer.group_send(self.group_name, {'type':'presence.join','user_id':str(user.id)})

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        user = self.scope.get('user')
        await self.channel_layer.group_send(self.group_name, {'type':'presence.leave','user_id':str(user.id)})

    async def receive_json(self, content):
        action = content.get('action')
        user = self.scope.get('user')
        if action == 'send_message':
            data = content.get('data', {})
            msg = await database_sync_to_async(self._create_message)(user, data)
            serialized = MessageSerializer(msg).data
            await self.channel_layer.group_send(self.group_name, {'type':'chat.message','message':serialized})
        elif action == 'typing':
            await self.channel_layer.group_send(self.group_name, {'type':'chat.typing','user_id':str(user.id)})
        elif action == 'mark_read':
            await database_sync_to_async(self._mark_read)(user)

    def _create_message(self, user, data):
        conv = Conversation.objects.get(id=self.conversation_id)
        msg = Message.objects.create(
            conversation=conv,
            sender=user,
            content=data.get('content'),
            attachments=data.get('attachments', [])
        )
        # create receipts for other participants
        participants = conv.participants.exclude(user=user)
        for p in participants:
            MessageReceipt.objects.get_or_create(message=msg, user=p.user)
        return msg

    def _mark_read(self, user):
        conv = Conversation.objects.get(id=self.conversation_id)
        try:
            p = conv.participants.get(user=user)
            p.last_read_at = timezone.now()
            p.save(update_fields=['last_read_at'])
        except Participant.DoesNotExist:
            pass
        MessageReceipt.objects.filter(message__conversation=conv, user=user, read_at__isnull=True).update(read_at=timezone.now())

    # group handlers
    async def chat_message(self, event):
        await self.send_json({'type':'message','message': event['message']})

    async def chat_typing(self, event):
        await self.send_json({'type':'typing','user_id': event.get('user_id')})

    async def presence_join(self, event):
        await self.send_json({'type':'presence','action':'join','user_id': event.get('user_id')})

    async def presence_leave(self, event):
        await self.send_json({'type':'presence','action':'leave','user_id': event.get('user_id')})
