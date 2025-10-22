from django.contrib import admin
from .models import VerificationRequest, Document, Selfie, VerificationAudit

@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ('id','user','status','tier','created_at','decision_at')
    list_filter = ('status','tier','created_at')
    search_fields = ('user__email','user__username','id')
    readonly_fields = ('created_at','updated_at','decision_at','expires_at')
    actions = ['approve_basic','approve_advanced','reject_request']

    def approve_basic(self, request, queryset):
        for q in queryset:
            q.mark_approved(tier='basic', actor=request.user, reason='admin_batch_approve')
    approve_basic.short_description = "Approve selected as Basic"

    def approve_advanced(self, request, queryset):
        for q in queryset:
            q.mark_approved(tier='advanced', actor=request.user, reason='admin_batch_approve_advanced')
    approve_advanced.short_description = "Approve selected as Advanced"

    def reject_request(self, request, queryset):
        for q in queryset:
            q.mark_rejected(actor=request.user, reason='admin_batch_reject')
    reject_request.short_description = "Reject selected requests"

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id','user','document_type','filename','uploaded_at','processed','redacted')
    search_fields = ('user__email','filename')

@admin.register(Selfie)
class SelfieAdmin(admin.ModelAdmin):
    list_display = ('id','user','uploaded_at','processed')
    search_fields = ('user__email',)

@admin.register(VerificationAudit)
class VerificationAuditAdmin(admin.ModelAdmin):
    list_display = ('id','request','verb','actor','created_at')
    readonly_fields = ('id','request','actor','verb','payload','created_at')
