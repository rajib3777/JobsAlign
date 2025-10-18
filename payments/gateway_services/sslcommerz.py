import requests
from django.conf import settings

def initiate_payment(user, amount, transaction):
    post_data = {
        "store_id": settings.SSLC_STORE_ID,
        "store_passwd": settings.SSLC_STORE_PASS,
        "total_amount": str(amount),
        "currency": "BDT",
        "tran_id": str(transaction.reference),
        "success_url": f"{settings.BACKEND_URL}/api/payments/sslcommerz/success/",
        "fail_url": f"{settings.BACKEND_URL}/api/payments/sslcommerz/fail/",
        "cancel_url": f"{settings.BACKEND_URL}/api/payments/sslcommerz/cancel/",
        "cus_name": user.full_name,
        "cus_email": user.email,
    }

    response = requests.post("https://sandbox.sslcommerz.com/gwprocess/v4/api.php", data=post_data)
    data = response.json()

    return {
        "redirect_url": data.get("GatewayPageURL"),
        "transaction_id": str(transaction.id),
        "reference": transaction.reference
    }

def verify_payment(data):
    if data.get("status") == "VALID":
        return {"status": "success", "tran_id": data.get("tran_id")}
    return {"status": "failed"}
