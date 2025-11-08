from rest_framework import serializers
from django.contrib.auth import password_validation, authenticate
from django.utils import timezone
from .utils import send_verification_email
from .models import User

# Helper to safely get related data (wallet/referral may be in other apps)
def safe_attr(obj, attr, default=None):
    try:
        return getattr(obj, attr)
    except Exception:
        return default


class WalletMiniSerializer(serializers.Serializer):
    """If payments.Wallet exists, this shows minimal wallet info."""
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_earned = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_spent = serializers.DecimalField(max_digits=12, decimal_places=2)


class ReferralMiniSerializer(serializers.Serializer):
    """If referral.ReferralAccount exists, minimal fields."""
    code = serializers.CharField()
    total_referred = serializers.IntegerField()
    total_bonus = serializers.DecimalField(max_digits=12, decimal_places=2)


class UserSerializer(serializers.ModelSerializer):
    profile_completion = serializers.ReadOnlyField()
    wallet = serializers.SerializerMethodField()
    referral = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'user_type', 'gender', 'date_of_birth',
            'profile_photo', 'cover_photo', 'tagline', 'bio','wallet','referral',
            'is_verified', 'is_identity_verified', 'identity_document',
            'country', 'city', 'address',
            'linkedin', 'github', 'website',
            'level', 'trust_score', 'skills', 'portfolio_url', 'portfolio_description',
            'total_projects', 'completed_orders', 'total_earnings',
            'followers', 'rating', 'total_reviews',
            'is_online', 'last_seen', 'date_joined', 'last_login', 'profile_completion', 
            'has_passed_basic_english_test', 'has_passed_category_test', 'has_video_intro'
        ]
        read_only_fields = [
            'id', 'rating', 'total_reviews', 'profile_completion',
            'date_joined', 'last_login', 'is_online', 'last_seen',
            'wallet', 'referral',
        ]

    def get_wallet(self, obj):
        wallet_obj = safe_attr(obj, 'wallet')
        if not wallet_obj:
            return None
        # attempt to serialize minimal wallet
        try:
            return {
                'balance': getattr(wallet_obj, 'balance', None),
                'total_earned': getattr(wallet_obj, 'total_earned', None),
                'total_spent': getattr(wallet_obj, 'total_spent', None),
            }
        except Exception:
            return None

    def get_referral(self, obj):
        ref_obj = safe_attr(obj, 'referral')
        if not ref_obj:
            return None
        try:
            return {
                'code': getattr(ref_obj, 'code', None) or getattr(ref_obj, 'referral_code', None),
                'total_referred': getattr(ref_obj, 'total_referred', 0),
                'total_bonus': getattr(ref_obj, 'total_bonus', None),
            }
        except Exception:
            return None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True, required=False, allow_blank=True)
    referral_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('email', 'full_name', 'user_type', 'password', 'password2', 'referral_code')

    def validate(self, attrs):
        pw = attrs.get('password')
        pw2 = attrs.pop('password2', None)
        if pw2 is not None and pw != pw2:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        password_validation.validate_password(pw, self.instance)
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        referral_code = validated_data.pop('referral_code', None)
        password = validated_data.pop('password')
        user = self.Meta.model.objects.create_user(password=password, **validated_data)

        # make user inactive until email verification
        user.is_active = False
        user.save()

        # send verification email
        if request:
            send_verification_email(request, user)

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(email=attrs.get('email'), password=attrs.get('password'))
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value, self.context.get('user'))
        return value
