from rest_framework import serializers
from .models import SubscriptionPlan, Coupon, UserSubscription, Invoice, BillingRecord

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'
        read_only_fields = ('id','created_at','updated_at')

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'
        read_only_fields = ('id','used_count','created_at')

class SubscribeSerializer(serializers.Serializer):
    plan_id = serializers.UUIDField()
    coupon = serializers.CharField(required=False, allow_blank=True)
    seats = serializers.IntegerField(required=False, default=1)
    payment_method = serializers.CharField(required=False, allow_blank=True)  # token / method id for gateway

class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer()
    coupon = CouponSerializer()
    class Meta:
        model = UserSubscription
        fields = '__all__'
        read_only_fields = ('id','started_at','updated_at','billing_customer_id')

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'
