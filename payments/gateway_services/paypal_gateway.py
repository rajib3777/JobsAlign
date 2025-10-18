import requests
from django.conf import settings

def initiate_payment(user, amount, transaction):
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {"currency_code": "USD", "value": str(amount)},
            "invoice_id": transaction.reference
        }],
        "application_context": {
            "return_url": f"{settings.BACKEND_URL}/api/payments/paypal/success/",
            "cancel_url": f"{settings.BACKEND_URL}/api/payments/paypal/cancel/"
        }
    }

    access_token = get_paypal_token()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}

    res = requests.post(f"{settings.PAYPAL_API_URL}/v2/checkout/orders", headers=headers, json=payload)
    order = res.json()
    approval_url = next((l["href"] for l in order["links"] if l["rel"] == "approve"), None)

    return {"redirect_url": approval_url, "transaction_id": str(transaction.id)}

def get_paypal_token():
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET)
    res = requests.post(f"{settings.PAYPAL_API_URL}/v1/oauth2/token", auth=auth, data={"grant_type": "client_credentials"})
    return res.json().get("access_token")

def verify_payment(order_id):
    access_token = get_paypal_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get(f"{settings.PAYPAL_API_URL}/v2/checkout/orders/{order_id}", headers=headers)
    data = res.json()
    return {"status": "success" if data.get("status") == "COMPLETED" else "failed"}
