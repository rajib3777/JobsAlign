from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

User = settings.AUTH_USER_MODEL

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True, null=True)
    is_group = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='created_conversations')
    is_archived = models.BooleanField(default=False)  # for soft-archive
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['updated_at'])]

    def __str__(self):
        return self.title or f"Conversation {self.id}"


class Participant(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    joined_at = models.DateTimeField(default=timezone.now)
    last_read_at = models.DateTimeField(blank=True, null=True)
    muted = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    class Meta:
        unique_together = ('conversation', 'user')


class MessageThread(models.Model):
    """Optional: messages can belong to a thread within a conversation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='threads')
    title = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(default=timezone.now)


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    thread = models.ForeignKey(MessageThread, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    content = models.TextField(blank=True, null=True)
    attachments = models.JSONField(default=list, blank=True)  # list of dicts: {url, name, type, size}
    created_at = models.DateTimeField(default=timezone.now)
    edited_at = models.DateTimeField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)  # soft-delete for UI
    edit_log = models.JSONField(default=list, blank=True)  # store previous_content/time/editor
    pinned = models.BooleanField(default=False)
    reactions = models.JSONField(default=dict, blank=True)  # {"emoji": [user_id,...]}

    class Meta:
        indexes = [models.Index(fields=['conversation', 'created_at']),]
        ordering = ['created_at']

    def add_reaction(self, emoji, user_id):
        arr = self.reactions.get(emoji, [])
        if user_id not in arr:
            arr.append(user_id)
        self.reactions[emoji] = arr
        self.save(update_fields=['reactions'])

    def remove_reaction(self, emoji, user_id):
        arr = self.reactions.get(emoji, [])
        if user_id in arr:
            arr.remove(user_id)
            if arr:
                self.reactions[emoji] = arr
            else:
                self.reactions.pop(emoji, None)
            self.save(update_fields=['reactions'])


class MessageReceipt(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='receipts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_receipts')
    delivered_at = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('message', 'user')
