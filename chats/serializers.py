from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Conversation, Participant, Message, MessageThread, MessageReceipt

User = get_user_model()

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','email','full_name')

class ParticipantSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    class Meta:
        model = Participant
        fields = ('id','user','joined_at','last_read_at','muted','is_admin')

class ConversationSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)
    class Meta:
        model = Conversation
        fields = ('id','title','is_group','created_by','is_archived','created_at','updated_at','participants')
        read_only_fields = ('created_at','updated_at','created_by')

class ConversationCreateSerializer(serializers.ModelSerializer):
    participant_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    class Meta:
        model = Conversation
        fields = ('title','is_group','participant_ids')

    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids', [])
        user = self.context['request'].user
        conv = Conversation.objects.create(created_by=user, **validated_data)
        Participant.objects.create(conversation=conv, user=user, is_admin=True)
        if participant_ids:
            User = get_user_model()
            users = User.objects.filter(id__in=participant_ids)
            for u in users:
                if u != user:
                    Participant.objects.get_or_create(conversation=conv, user=u)
        return conv

class MessageSerializer(serializers.ModelSerializer):
    sender = UserMiniSerializer(read_only=True)
    class Meta:
        model = Message
        fields = ('id','conversation','thread','sender','content','attachments','created_at','edited_at','is_deleted','pinned','reactions')
        read_only_fields = ('id','sender','created_at','edited_at','reactions')

class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('conversation','thread','content','attachments')

    def validate(self, attrs):
        conv = attrs['conversation']
        user = self.context['request'].user
        if not conv.participants.filter(user=user).exists():
            raise serializers.ValidationError('Not a participant')
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        msg = Message.objects.create(sender=user, **validated_data)
        return msg

class ThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageThread
        fields = ('id','conversation','title','created_by','created_at')

class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageReceipt
        fields = ('message','user','delivered_at','read_at')
