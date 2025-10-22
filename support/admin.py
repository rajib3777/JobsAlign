from django.contrib import admin
from .models import TicketCategory, SupportTicket, TicketMessage, CannedResponse, SupportAudit

@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ('name','slug','is_active','created_at')
    search_fields = ('name','slug')

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('subject','user','category','status','priority','assigned_to','updated_at')
    search_fields = ('subject','user__email','id')
    list_filter = ('status','priority','category')
    readonly_fields = ('created_at','updated_at','resolved_at')
    actions = ['mark_resolved_action']

    def mark_resolved_action(self, request, queryset):
        for t in queryset:
            t.mark_resolved(actor=request.user, note='Bulk resolved by admin')
    mark_resolved_action.short_description = "Mark selected tickets as resolved"

@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ('ticket','sender','internal','system','created_at')
    search_fields = ('ticket__subject','sender__email','id')

@admin.register(CannedResponse)
class CannedResponseAdmin(admin.ModelAdmin):
    list_display = ('title','slug','created_by','created_at')

@admin.register(SupportAudit)
class SupportAuditAdmin(admin.ModelAdmin):
    list_display = ('ticket','verb','actor','created_at')
    readonly_fields = ('ticket','verb','actor','payload','created_at')
