from django.contrib import admin
from .models import Conversation, Participant, Message, MessageReceipt, MessageThread

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id','title','is_group','created_by','created_at')
    search_fields = ('title',)

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('conversation','user','joined_at','last_read_at','is_admin')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id','conversation','sender','created_at','is_deleted','pinned')
    search_fields = ('content',)
    readonly_fields = ('edit_log',)

@admin.register(MessageReceipt)
class MessageReceiptAdmin(admin.ModelAdmin):
    list_display = ('message','user','delivered_at','read_at')

@admin.register(MessageThread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('id','conversation','title','created_by','created_at')
