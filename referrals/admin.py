from django.contrib import admin
from .models import ReferralCode, Referral, ReferralCommission

@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "total_signups", "total_earnings")
    search_fields = ("user__username","code")

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ("referrer","referred","code_used","status","created_at","total_commission")
    search_fields = ("referrer__username","referred__username","code_used")
    list_filter = ("status",)

@admin.register(ReferralCommission)
class ReferralCommissionAdmin(admin.ModelAdmin):
    list_display = ("referral","transaction_id","earned_amount","created_at","paid")
    search_fields = ("transaction_id","referral__referrer__username")
    list_filter = ("paid",)

