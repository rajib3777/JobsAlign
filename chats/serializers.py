from rest_framework import serializers
from .models import Conversation, Message, MessageAttachment
from django.contrib.auth import get_user_model

User = get_user_model()

class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = ("id","filename","file","filesize","uploaded_at")

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    attachments = MessageAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = ("id","conversation","sender","text","is_system","metadata","edited_at","is_deleted","created_at","attachments")
        read_only_fields = ("id","sender","created_at","edited_at","is_system","attachments")

    def get_sender(self, obj):
        if obj.sender:
            return {"id": obj.sender.id, "full_name": getattr(obj.sender, "full_name", str(obj.sender))}
        return None

class MessageCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.ListField(child=serializers.FileField(), write_only=True, required=False)

    class Meta:
        model = Message
        fields = ("conversation","text","attachments")

    def validate(self, attrs):
        user = self.context['request'].user
        conv = attrs.get("conversation")
        if not conv.participants.filter(id=user.id).exists():
            raise serializers.ValidationError("You are not a participant of this conversation.")
        return attrs

    def create(self, validated_data):
        files = validated_data.pop("attachments", [])
        user = self.context['request'].user
        message = Message.objects.create(sender=user, **validated_data)
        for f in files:
            MessageAttachment.objects.create(message=message, file=f)
        return message

class ConversationSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id","title","participants","is_group","project","contract","created_at","updated_at","last_message")
        read_only_fields = ("id","created_at","updated_at","last_message")

    def get_participants(self, obj):
        return [{"id": u.id, "full_name": getattr(u, "full_name", str(u))} for u in obj.participants.all()]

    def get_last_message(self, obj):
        last = obj.messages.order_by("-created_at").first()
        if last:
            return MessageSerializer(last).data
        return None

class ConversationCreateSerializer(serializers.ModelSerializer):
    participant_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True)

    class Meta:
        model = Conversation
        fields = ("title","participant_ids","is_group","project","contract")

    def validate_participant_ids(self, v):
        # optionally validate participant existence
        return v

    def create(self, validated_data):
        pids = validated_data.pop("participant_ids", [])
        conv = Conversation.objects.create(**validated_data)
        conv.participants.set(pids)
        return conv
