from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .serializers import MessageSerializer
from datetime import datetime, timedelta
from django.conf import settings
import jwt

def broadcast_message(message):
    channel_layer = get_channel_layer()
    group = f"conversation_{message.conversation.id}"
    payload = {
        "type": "chat.message",
        "message": MessageSerializer(message).data
    }
    async_to_sync(channel_layer.group_send)(group, payload)

# WS token helper (ephemeral token) - sign short lived tokens for websocket auth
def make_ws_token(user, conversation_id, ttl_seconds=300):
    payload = {
        "user_id": user.id,
        "conversation_id": str(conversation_id),
        "exp": datetime.utcnow() + timedelta(seconds=ttl_seconds),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token

# moderation hook - placeholder (call external content moderation service here)
def moderate_message_text(text):
    """
    Return dict {'blocked': bool, 'reason': str or None}
    Placeholder for integration with external moderation/AI.
    """
    # e.g. implement banned words / external API call
    banned = ["spamword1","spamword2"]
    for b in banned:
        if b in (text or "").lower():
            return {"blocked": True, "reason": "Contains forbidden word"}
    return {"blocked": False, "reason": None}
