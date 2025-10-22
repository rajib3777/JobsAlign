from django.conf import settings
from .models import CannedResponse
import random
import requests

def classify_ticket_intent(text):
    """
    Return (intent, priority). Placeholder: integrate with NLP service.
    Example intents: 'payment_issue', 'verification', 'technical', 'dispute', 'other'
    Priority: low|medium|high|urgent
    """
    txt = (text or "").lower()
    if any(w in txt for w in ['refund','charge','billing','invoice','payment']):
        return 'payment_issue', 'high'
    if any(w in txt for w in ['verify','id','passport','nid','kyc']):
        return 'verification', 'medium'
    if any(w in txt for w in ['error','bug','crash','fail']):
        return 'technical', 'high'
    if any(w in txt for w in ['scam','fraud','dispute']):
        return 'dispute', 'urgent'
    # fallback random suggestion
    return 'general', random.choice(['low','medium'])

def generate_auto_reply(ticket):
    """
    Use canned responses or call AI to craft reply. Placeholder.
    Returns reply string or None.
    """
    # 1) if simple category -> pick canned response matching slug
    intent = ticket.meta.get('intent') if ticket.meta else None
    if intent:
        # try to find canned response with slug == intent
        cr = CannedResponse.objects.filter(slug__icontains(intent).exists()
                                           ).first() if hasattr(CannedResponse.objects, 'filter') else None
        if cr:
            return cr.content
    # 2) fallback simple message
    return "Thanks for contacting JobsAlign Support. We've received your ticket and will respond shortly."

def sanitize_attachments(attachments):
    """
    Placeholder: validate URLs, check S3 signed, virus-scan results, etc.
    """
    return attachments or []
