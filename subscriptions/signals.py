from django.db.models.signals import post_save
from django.dispatch import receiver
from payments.models import Transaction
from .utils import create_subscription_and_invoice
from .models import Coupon
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

@receiver(post_save, sender=Transaction)
def activate_subscription_on_payment(sender, instance, created, **kwargs):
    """
    When a Transaction for a subscription succeeds, create/activate subscription.
    This expects transactions to have type='subscription' and to be updated by payments gateway.
    """
    if not created and instance.type == 'subscription' and instance.status == 'success':
        # guard: ensure we don't double create
        metadata = instance.metadata if hasattr(instance, 'metadata') else {}
        plan_slug = metadata.get('plan_slug') or instance.meta.get('plan_slug') if hasattr(instance, 'meta') else None
        coupon_code = metadata.get('coupon') or instance.meta.get('coupon') if hasattr(instance, 'meta') else None
        seats = int(metadata.get('seats', 1) or 1)

        try:
            from .models import SubscriptionPlan
            plan = SubscriptionPlan.objects.filter(slug=plan_slug).first()
            coupon = Coupon.objects.filter(code=coupon_code).first() if coupon_code else None
            if plan:
                user = instance.user
                # create subscription & invoice (mark paid)
                sub, invoice = create_subscription_and_invoice(user, plan, coupon=coupon, seats=seats, payment_reference=instance.reference, gateway_response={"tx_id": str(instance.id)})
                # update transaction linking
                instance.meta = {**getattr(instance, 'meta', {}), 'subscription_id': str(sub.id)}
                instance.save(update_fields=['meta'])
        except Exception as e:
            print(f"[subscriptions.signals] Failed to activate subscription: {e}")
