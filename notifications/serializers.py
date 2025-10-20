from rest_framework import serializers
from .models import Notification, NotificationPreference

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('id','created_at','updated_at','is_push_sent')

class NotificationCreateSerializer(serializers.Serializer):
    # helper serializer if external apps want a compact API to create notifications
    user_id = serializers.UUIDField()
    verb = serializers.CharField()
    title = serializers.CharField()
    message = serializers.CharField(required=False, allow_blank=True)
    actor_id = serializers.UUIDField(required=False)
    data = serializers.JSONField(required=False)
    group_key = serializers.CharField(required=False, allow_blank=True)
    level = serializers.ChoiceField(choices=[lv[0] for lv in Notification.LEVELS], required=False)

class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = '__all__'
        read_only_fields = ('id','user','created_at')
