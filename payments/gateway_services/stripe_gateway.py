import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def initiate_payment(user, amount, transaction):
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': 'JobsAlign Deposit'},
                'unit_amount': int(amount * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=f"{settings.BACKEND_URL}/api/payments/stripe/success/?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.BACKEND_URL}/api/payments/stripe/cancel/",
        metadata={"transaction_id": str(transaction.id)}
    )

    return {"redirect_url": session.url, "transaction_id": str(transaction.id)}

def verify_payment(session_id):
    session = stripe.checkout.Session.retrieve(session_id)
    if session.payment_status == "paid":
        return {"status": "success", "trx_id": session.id}
    return {"status": "failed"}
