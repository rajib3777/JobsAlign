from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import SubscriptionPlan, UserSubscription, Coupon
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

class SubscriptionsBasicTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='a@example.com', password='pass')
        self.plan = SubscriptionPlan.objects.create(slug='pro-monthly', name='Pro Monthly', price=Decimal('29.99'), billing_period='monthly')
        self.coupon = Coupon.objects.create(code='TEST10', percent_off=10)

    def test_create_subscription_and_invoice(self):
        from .utils import create_subscription_and_invoice
        sub, invoice = create_subscription_and_invoice(self.user, self.plan, coupon=self.coupon, seats=1, payment_reference='tx-123')
        self.assertTrue(sub.id)
        self.assertEqual(invoice.paid, True)
        self.assertEqual(invoice.amount, self.coupon.apply_discount(self.plan.price))
