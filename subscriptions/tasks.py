from celery import shared_task
from django.utils import timezone
from .models import UserSubscription, Invoice, BillingRecord, SubscriptionPlan
from decimal import Decimal
from django.conf import settings
from . import utils
import datetime


@shared_task(bind=True)
def run_recurring_billing(self, batch_size=100):
    """
    Charge all subscriptions whose current_period_end <= now and auto_renew True.
    """
    now = timezone.now()
    due = UserSubscription.objects.filter(current_period_end__lte=now, auto_renew=True, status__in=['active','trialing'])
    count = 0
    for sub in due[:batch_size]:
        try:
            plan = sub.plan
            # compute price (coupon applied only at initial purchase or if coupon persistent)
            coupon = sub.coupon
            amount = utils.calculate_price_after_coupon(plan, coupon)
            # create invoice
            invoice = Invoice.objects.create(subscription=sub, amount=amount, currency=plan.currency)
            # create billing record
            BillingRecord.objects.create(user=sub.user, invoice=invoice, amount=amount, currency=plan.currency, type='subscription_attempt', meta={'subscription_id': str(sub.id)})
            # trigger payment via payments app
            # Here we create a Transaction and expect payments app to process and call back Transaction.status update
            from payments.models import Transaction
            txn = Transaction.objects.create(user=sub.user, gateway=None, type='subscription', amount=amount, reference=f"SUB_RECUR-{sub.id}-{timezone.now().timestamp()}")
            sub.last_payment_attempt = timezone.now()
            sub.save(update_fields=['last_payment_attempt'])
            count += 1
        except Exception as e:
            print(f"[subscriptions.tasks] Billing error for sub {sub.id}: {e}")
            continue
    return {"billed": count}

@shared_task
def retry_failed_payments():
    """
    Implement dunning: retry subscriptions in past_due status.
    """
    now = timezone.now()
    retry_window = now - timezone.timedelta(days=7)
    subs = UserSubscription.objects.filter(status='past_due', last_payment_attempt__lte=retry_window)
    for sub in subs:
        try:
            # attempt a new Transaction
            from payments.models import Transaction
            amount = utils.calculate_price_after_coupon(sub.plan, sub.coupon)
            txn = Transaction.objects.create(user=sub.user, gateway=None, type='subscription', amount=amount, reference=f"SUB_RETRY-{sub.id}-{timezone.now().timestamp()}")
            sub.last_payment_attempt = timezone.now()
            sub.save(update_fields=['last_payment_attempt'])
        except Exception as e:
            print(f"[subscriptions.tasks] Retry failed for {sub.id}: {e}")
            continue

@shared_task
def send_subscription_reminders():
    """
    Notify users whose subscriptions will expire within X days.
    """
    from notifications.utils import create_notification
    now = timezone.now()
    warn_date = now + timezone.timedelta(days=3)
    subs = UserSubscription.objects.filter(current_period_end__lte=warn_date, status='active')
    for sub in subs:
        create_notification(user=sub.user, verb='sub_renewal_warning', title='Your subscription will renew soon', message=f'Your plan {sub.plan.name} renews on {sub.current_period_end.date()}')
