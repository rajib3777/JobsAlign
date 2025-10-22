from django.urls import path
from . import api_views

urlpatterns = [
    path('plans/', api_views.PlanListView.as_view(), name='subscription-plans'),
    path('subscribe/', api_views.SubscribeView.as_view(), name='subscribe'),
    path('my/', api_views.MySubscriptionView.as_view(), name='my-subscription'),
    path('cancel/<uuid:subscription_id>/', api_views.CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('invoices/', api_views.InvoiceListView.as_view(), name='invoices'),
    path('coupon/validate/', api_views.CouponValidateView.as_view(), name='coupon-validate'),
]
