from .models import Transaction
import uuid

def initiate_payment_gateway(user, gateway, amount):
    reference = f"{gateway.name.upper()}-{uuid.uuid4().hex[:8]}"
    transaction = Transaction.objects.create(
        user=user,
        gateway=gateway,
        type="deposit",
        amount=amount,
        reference=reference
    )
    
    return {
        "transaction_id": str(transaction.id),
        "reference": reference,
        "gateway": gateway.name,
        "redirect_url": f"/payments/{gateway.name.lower()}/checkout/{reference}/"
    }
