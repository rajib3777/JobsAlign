from django.contrib import admin
from .models import Notification, NotificationPreference

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id','user','verb','title','read','archived','created_at')
    search_fields = ('title','message','user__email')
    list_filter = ('read','archived','level')
    readonly_fields = ('id','created_at','updated_at')

@admin.register(NotificationPreference)
class PreferenceAdmin(admin.ModelAdmin):
    list_display = ('id','user','channel','notification_type','enabled')
    search_fields = ('user__email','notification_type')

