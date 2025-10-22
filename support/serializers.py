from rest_framework import serializers
from .models import TicketCategory, SupportTicket, TicketMessage, CannedResponse, SupportAudit

class TicketCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketCategory
        fields = '__all__'
        read_only_fields = ('id','created_at')

class TicketMessageSerializer(serializers.ModelSerializer):
    sender_display = serializers.SerializerMethodField()
    class Meta:
        model = TicketMessage
        fields = '__all__'
        read_only_fields = ('id','created_at','system')

    def get_sender_display(self, obj):
        if not obj.sender:
            return None
        return getattr(obj.sender, 'username', str(obj.sender))

class SupportTicketSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)
    class Meta:
        model = SupportTicket
        fields = '__all__'
        read_only_fields = ('id','user','created_at','updated_at','resolved_at')

class CreateTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = ('subject','category','priority')

class CreateMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketMessage
        fields = ('ticket','content','internal','attachments')

class CannedResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CannedResponse
        fields = '__all__'
        read_only_fields = ('id','created_at')
