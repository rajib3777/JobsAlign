from payments.models import Transaction
from django.utils import timezone

def start_subscription_payment(user, plan):
    txn = Transaction.objects.create(
        user=user,
        type="subscription",
        amount=plan.price,
        reference=f"SUB-{user.id}-{plan.id}-{timezone.now().timestamp()}",
    )
    return txn
