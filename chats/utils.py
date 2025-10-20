from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .serializers import MessageSerializer
from .models import Message
from django.conf import settings

channel_layer = get_channel_layer()

def notify_message_created(message):
    try:
        serialized = MessageSerializer(message).data
        group = f'chat_{message.conversation_id}'
        async_to_sync(channel_layer.group_send)(group, {'type':'chat.message','message':serialized})
    except Exception:
        pass
    # enqueue background notifications
    try:
        from .tasks import send_message_notifications
        send_message_notifications.delay(str(message.id))
    except Exception:
        pass

def notify_reaction_updated(message, emoji, user):
    try:
        group = f'chat_{message.conversation_id}'
        async_to_sync(channel_layer.group_send)(group, {'type':'reaction.updated','message_id': str(message.id), 'emoji':emoji, 'user_id': str(user.id)})
    except Exception:
        pass

def notify_message_edited(message):
    try:
        serialized = MessageSerializer(message).data
        group = f'chat_{message.conversation_id}'
        async_to_sync(channel_layer.group_send)(group, {'type':'message.edited','message':serialized})
    except Exception:
        pass

def notify_message_pinned(message):
    try:
        serialized = MessageSerializer(message).data
        group = f'chat_{message.conversation_id}'
        async_to_sync(channel_layer.group_send)(group, {'type':'message.pinned','message':serialized})
    except Exception:
        pass
