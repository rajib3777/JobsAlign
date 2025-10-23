from rest_framework import serializers
from .models import ReferralCode, Referral, ReferralCommission

class ReferralCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralCode
        fields = ("user", "code", "created_at", "total_signups", "total_earnings")
        read_only_fields = fields

class ReferralSerializer(serializers.ModelSerializer):
    referrer_username = serializers.SerializerMethodField()
    referred_username = serializers.SerializerMethodField()

    class Meta:
        model = Referral
        fields = "__all__"
        read_only_fields = ("id","referrer","created_at","activated_at","total_commission")

    def get_referrer_username(self, obj):
        return getattr(obj.referrer, "username", None)

    def get_referred_username(self, obj):
        return getattr(obj.referred, "username", None) if obj.referred else None

class ReferralCommissionSerializer(serializers.ModelSerializer):
    referral_referrer = serializers.SerializerMethodField()
    class Meta:
        model = ReferralCommission
        fields = "__all__"
        read_only_fields = fields

    def get_referral_referrer(self, obj):
        return getattr(obj.referral.referrer, "username", None)
