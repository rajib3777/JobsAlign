from rest_framework import serializers
from .models import Wallet, Transaction, PaymentGateway

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['balance', 'total_earned', 'total_spent', 'currency']

class TransactionSerializer(serializers.ModelSerializer):
    gateway = serializers.StringRelatedField()
    class Meta:
        model = Transaction
        fields = '__all__'

class PaymentInitSerializer(serializers.Serializer):
    gateway = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

