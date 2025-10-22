from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import SubscriptionPlan, Coupon, UserSubscription, Invoice
from .serializers import PlanSerializer, CouponSerializer, UserSubscriptionSerializer, InvoiceSerializer, SubscribeSerializer
from . import utils
from django.utils import timezone
from decimal import Decimal

class PlanListView(generics.ListAPIView):
    queryset = SubscriptionPlan.objects.filter(active=True).order_by('-priority_tier')
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]

class CouponValidateView(generics.GenericAPIView):
    serializer_class = CouponSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get('code')
        try:
            coupon = Coupon.objects.get(code=code)
            if not coupon.is_valid():
                return Response({'valid': False, 'reason': 'expired_or_inactive'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'valid': True, 'discounted_price': str(coupon.apply_discount(Decimal(request.data.get('amount', '0'))))})
        except Coupon.DoesNotExist:
            return Response({'valid': False}, status=status.HTTP_404_NOT_FOUND)

class SubscribeView(generics.GenericAPIView):
    serializer_class = SubscribeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        plan = get_object_or_404(SubscriptionPlan, id=data['plan_id'])
        coupon = None
        if data.get('coupon'):
            coupon = Coupon.objects.filter(code=data['coupon']).first()
            if coupon and not coupon.is_valid():
                return Response({'detail':'Invalid coupon'}, status=status.HTTP_400_BAD_REQUEST)

        # create transaction via payments
        payment = utils.trigger_subscription_payment(request.user, plan, coupon=coupon, seats=data.get('seats',1), payment_method=data.get('payment_method'))
        if not payment.get('success'):
            return Response({'detail':'Payment initiation failed','error': payment.get('error')}, status=status.HTTP_400_BAD_REQUEST)

        # return transaction id for frontend to complete checkout
        return Response({'transaction_id': payment.get('transaction_id'), 'amount': str(payment.get('amount'))}, status=status.HTTP_200_OK)

class MySubscriptionView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSubscriptionSerializer

    def get_object(self):
        sub = UserSubscription.objects.filter(user=self.request.user, status__in=['active','trialing','past_due']).order_by('-created_at').first()
        if not sub:
            # return empty 404
            raise generics.Http404
        return sub

class CancelSubscriptionView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, subscription_id):
        sub = get_object_or_404(UserSubscription, id=subscription_id, user=request.user)
        sub.auto_renew = False
        sub.status = 'cancelled'
        sub.grace_period_until = timezone.now() + timezone.timedelta(days=7)  # e.g., keep grace for 7 days
        sub.save(update_fields=['auto_renew','status','grace_period_until'])
        # log billing record
        from .models import BillingRecord
        BillingRecord.objects.create(user=request.user, invoice=None, amount=0, type='subscription_cancel', meta={'subscription_id': str(sub.id)})
        return Response({'detail':'cancelled'}, status=status.HTTP_200_OK)

class InvoiceListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        return Invoice.objects.filter(subscription__user=self.request.user).order_by('-created_at')

