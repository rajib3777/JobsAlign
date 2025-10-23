from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Referral, ReferralCode, ReferralCommission
from .serializers import ReferralCodeSerializer, ReferralSerializer, ReferralCommissionSerializer
from .utils import create_referral_code_for_user, get_referrer_for_code

class MyReferralCodeView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReferralCodeSerializer

    def get_object(self):
        return create_referral_code_for_user(self.request.user)

class MyReferralsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReferralSerializer

    def get_queryset(self):
        return Referral.objects.filter(referrer=self.request.user).order_by("-created_at")

class ApplyReferralView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, code):
        # user applying a referral code to themselves (if allowed)
        rc = get_referrer_for_code(code)
        if not rc:
            return Response({"detail":"Referral code not found"}, status=status.HTTP_404_NOT_FOUND)
        # prevent self-apply
        if rc.id == request.user.id:
            return Response({"detail":"Cannot apply your own code"}, status=status.HTTP_400_BAD_REQUEST)
        # create Referral if not exists
        from .models import Referral
        existing = Referral.objects.filter(referrer=rc, referred=request.user).exists()
        if existing:
            return Response({"detail":"Referral already applied"}, status=status.HTTP_400_BAD_REQUEST)
        Referral.objects.create(referrer=rc, referred=request.user, code_used=code, created_at=timezone.now())
        # increment totals
        rr = ReferralCode.objects.get(user=rc)
        rr.total_signups += 1
        rr.save(update_fields=["total_signups"])
        return Response({"ok": True, "message":"Referral applied"})

class MyCommissionsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReferralCommissionSerializer

    def get_queryset(self):
        # show commissions for referrals made by this user
        return ReferralCommission.objects.filter(referral__referrer=self.request.user).order_by("-created_at")
