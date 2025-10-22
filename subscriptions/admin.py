from django.contrib import admin
from .models import SubscriptionPlan, Coupon, UserSubscription, Invoice, BillingRecord

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name','slug','price','billing_period','active','priority_tier')
    search_fields = ('name','slug')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code','percent_off','amount_off','active','expires_at','used_count')
    search_fields = ('code',)

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user','plan','status','started_at','current_period_end','auto_renew')
    search_fields = ('user__email','plan__name')
    readonly_fields = ('created_at','updated_at')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id','subscription','amount','paid','paid_at','created_at')
    search_fields = ('subscription__user__email',)

@admin.register(BillingRecord)
class BillingRecordAdmin(admin.ModelAdmin):
    list_display = ('id','user','amount','type','created_at')
    search_fields = ('user__email','type')

