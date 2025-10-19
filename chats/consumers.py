import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from .models import Conversation, Message
from .utils import moderate_message_text
from django.contrib.auth import get_user_model
from django.conf import settings
import jwt
from datetime import datetime
User = get_user_model()

# simple in-memory rate limit per connection (production: use Redis)
MAX_MESSAGES_PER_MINUTE = 60

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        qs = parse_qs(self.scope['query_string'].decode())
        token = qs.get('token', [None])[0]
        conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        user = await self.get_user_from_token(token)
        if not user:
            await self.close(code=4003)
            return
        self.scope['user'] = user
        self.user = user
        self.conversation_id = conversation_id
        self.group_name = f"conversation_{conversation_id}"
        conv = await database_sync_to_async(lambda: Conversation.objects.filter(id=conversation_id).first())()
        if not conv:
            await self.close(code=4004)
            return
        is_member = await database_sync_to_async(lambda: conv.participants.filter(id=user.id).exists())()
        if not is_member:
            await self.close(code=4005)
            return

        # rate-limiting state
        self.msg_count = 0
        self.msg_window_start = datetime.utcnow()

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        except Exception:
            pass

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            return
        try:
            data = json.loads(text_data)
        except Exception:
            return

        # simple rate-limiting sliding window (production: use Redis counters)
        now = datetime.utcnow()
        delta = (now - self.msg_window_start).total_seconds()
        if delta > 60:
            self.msg_window_start = now
            self.msg_count = 0
        self.msg_count += 1
        if self.msg_count > MAX_MESSAGES_PER_MINUTE:
            await self.send(json.dumps({"error":"rate_limit_exceeded"}))
            return

        if data.get("type") == "message.create":
            text = data.get("text","").strip()
            # moderation
            mod = moderate_message_text(text)
            if mod.get("blocked"):
                await self.send(json.dumps({"error":"message_blocked","reason":mod.get("reason")}))
                return
            # save message
            msg = await database_sync_to_async(lambda: Message.objects.create(conversation_id=self.conversation_id, sender=self.user, text=text))()
            # broadcast
            payload = {"type":"chat.message", "message":{
                "id": str(msg.id),
                "conversation": str(msg.conversation_id),
                "text": msg.text,
                "sender": {"id": self.user.id, "full_name": getattr(self.user, "full_name", str(self.user))},
                "created_at": msg.created_at.isoformat()
            }}
            await self.channel_layer.group_send(self.group_name, {"type":"chat.message", "message": payload["message"]})

    async def chat_message(self, event):
        # forward to WebSocket
        await self.send(text_data=json.dumps(event["message"]))

    @database_sync_to_async
    def get_user_from_token(self, token):
        if not token:
            return None
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            # optionally verify conversation_id matches payload
            return User.objects.filter(id=user_id).first()
        except Exception:
            return None
