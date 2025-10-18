import requests, uuid, json
from django.conf import settings

def initiate_payment(user, amount, transaction):
    base_url = "https://tokenized.pay.bka.sh/v1.2.0-beta"
    token_url = f"{base_url}/tokenized/checkout/create"
    headers = {
        "Authorization": f"Bearer {settings.BKASH_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "mode": "0011",
        "payerReference": user.email,
        "callbackURL": f"{settings.BACKEND_URL}/api/payments/bkash/callback/",
        "amount": str(amount),
        "currency": "BDT",
        "intent": "sale",
        "merchantInvoiceNumber": str(uuid.uuid4())
    }

    res = requests.post(token_url, headers=headers, data=json.dumps(payload))
    data = res.json()

    return {
        "redirect_url": data.get("bkashURL"),
        "transaction_id": str(transaction.id),
        "reference": transaction.reference
    }

def verify_payment(data):
    # after callback verify the transaction status
    return {
        "status": "success" if data.get("statusCode") == "0000" else "failed",
        "trxID": data.get("trxID")
    }
