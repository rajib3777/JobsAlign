from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from .models import SubscriptionPlan, Coupon, UserSubscription, Invoice, BillingRecord
from payments.models import Transaction
from django.contrib.auth import get_user_model

User = get_user_model()

# Gateway helpers (placeholders). Implement or wire to your gateway lib.
def create_checkout_session_stripe(user: User, amount: Decimal, currency: str, metadata: dict):
    """
    Return dict with 'url' or 'session_id' for frontend to redirect.
    In production implement Stripe Checkout API call here.
    """
    # placeholder create and return dummy checkout URL
    return {
        "success": True,
        "checkout_url": f"https://pay.example.com/checkout?user={user.id}&amount={amount}"
    }

def calculate_price_after_coupon(plan: SubscriptionPlan, coupon: Coupon):
    price = plan.price
    if coupon and coupon.is_valid():
        return coupon.apply_discount(price)
    return price

def create_subscription_and_invoice(user, plan, coupon=None, seats=1, payment_reference=None, gateway_response=None):
    """
    Create UserSubscription (trialing or active depending on trial_days) and Invoice/BillingRecord.
    This function should be called after successful payment.
    """
    now = timezone.now()
    # Calculate period end
    if plan.trial_days and plan.trial_days > 0:
        started_at = now
        period_end = now + timezone.timedelta(days=plan.trial_days)
        status = 'trialing'
    else:
        started_at = now
        if plan.billing_period == 'monthly':
            period_end = now + timezone.timedelta(days=30)
        else:
            period_end = now + timezone.timedelta(days=365)
        status = 'active'

    sub = UserSubscription.objects.create(
        user=user,
        plan=plan,
        coupon=coupon,
        status=status,
        started_at=started_at,
        current_period_end=period_end,
        seats=seats,
        billing_customer_id=None  # set after gateway customer creation
    )

    # create invoice record
    invoice_amount = calculate_price_after_coupon(plan, coupon)
    invoice = Invoice.objects.create(subscription=sub, amount=invoice_amount, currency=plan.currency, paid=True if payment_reference else False, reference=payment_reference or None, gateway_response=gateway_response or {})
    BillingRecord.objects.create(user=user, invoice=invoice, amount=invoice.amount, currency=invoice.currency, type='subscription_charge', meta={'plan': str(plan.id)})
    return sub, invoice

def trigger_subscription_payment(user, plan, coupon=None, seats=1, payment_method=None):
    """
    Initiate payment via payments app; create a Transaction to be processed by gateway.
    """
    # compute final price
    final_amount = calculate_price_after_coupon(plan, coupon)
    # call Payments API (use Transaction model if available)
    try:
        txn = Transaction.objects.create(user=user, gateway=None, type='subscription', amount=final_amount, reference=f"SUB-{user.id}-{plan.slug}-{timezone.now().timestamp()}")
        # If you have gateway integration, call gateway flow and attach txn.reference / metadata
        return {"success": True, "transaction_id": str(txn.id), "amount": final_amount}
    except Exception as e:
        return {"success": False, "error": str(e)}
