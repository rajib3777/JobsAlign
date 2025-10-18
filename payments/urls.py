from django.urls import path
from .api_views import WalletDetailView, TransactionListView, PaymentInitView

urlpatterns = [
    path("wallet/", WalletDetailView.as_view(), name="wallet"),
    path("transactions/", TransactionListView.as_view(), name="transactions"),
    path("initiate/", PaymentInitView.as_view(), name="payment-init"),
]
