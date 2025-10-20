from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Wallet, Transaction, PaymentGateway
from .serializers import WalletSerializer, TransactionSerializer, PaymentInitSerializer
from .utils import initiate_payment_gateway
from django.shortcuts import get_object_or_404
from .utils import send_payment_system_message


class WalletDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WalletSerializer
    def get_object(self):
        return self.request.user.wallet

class TransactionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionSerializer
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

class PaymentInitView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentInitSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        gateway_name = serializer.validated_data['gateway']
        amount = serializer.validated_data['amount']
        gateway = get_object_or_404(PaymentGateway, name=gateway_name, active=True)
        response = initiate_payment_gateway(request.user, gateway, amount)
        return Response(response, status=status.HTTP_200_OK)

