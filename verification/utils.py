import hashlib, os, io
from django.conf import settings
from PIL import Image
import requests

# ---- Virus scan stub ----
def virus_scan_file(file_obj):
    """
    Placeholder - integrate ClamAV or 3rd party scanner.
    Returns dict: {'clean': True, 'scanner': 'clamav', 'details': ...}
    """
    # implement actual call in prod
    return {'clean': True}

# ---- OCR adapter (pluggable) ----
def run_ocr_on_document(file_obj, document_type):
    """
    Run OCR via external provider (Onfido, Google Vision, AWS Textract, Tesseract).
    Return standardized dict, e.g. {'name':..., 'dob':..., 'doc_number':..., 'confidence':0.95}
    """
    provider = settings.VERIFICATION.get('OCR_PROVIDER', 'onfido')
    # Placeholder naive implementation:
    # In prod call Onfido/GoogleVision API and parse results.
    try:
        # read as bytes
        data = file_obj.read()
        # compute sha
        sha = hashlib.sha256(data).hexdigest()
        # reset file pointer if necessary
        try:
            file_obj.seek(0)
        except Exception:
            pass
        return {'provider': provider, 'doc_hash_sha256': sha, 'confidence': 0.8}
    except Exception as e:
        return {'error': str(e), 'confidence': 0.0}

# ---- Face match adapter ----
def run_face_match(selfie_file, verification_request):
    """
    Compare selfie to user document(s). Returns score (0..1) and details.
    Providers: AWS Rekognition, Face++ etc.
    """
    provider = settings.VERIFICATION.get('FACE_MATCH_PROVIDER', 'rekognition')
    # Placeholder: return 0.0..1.0 random or naive method
    try:
        # naive: return 0.5 as placeholder
        return 0.5, {'provider': provider}
    except Exception as e:
        return 0.0, {'error': str(e)}

# ---- Notification + badge grant ----
def notify_user_verification_status(user, request):
    try:
        from notifications.utils import create_notification
        if request.status.startswith('approved'):
            create_notification(user=user, verb='verification_approved', title='Verification approved', message=f'Your verification was approved: {request.status}', data={'request_id': str(request.id)})
        elif request.status == 'rejected':
            create_notification(user=user, verb='verification_rejected', title='Verification rejected', message=f'Your verification was rejected: {request.decision_reason}', data={'request_id': str(request.id)})
        else:
            create_notification(user=user, verb='verification_update', title='Verification update', message=f'Your verification status: {request.status}', data={'request_id': str(request.id)})
    except Exception:
        pass

def grant_verification_badge(user, tier='basic'):
    """
    Persist badge on user profile and update analytics/trust index.
    """
    try:
        profile = getattr(user, 'profile', None)
        # Example: profile.verified_tier = tier; profile.save()
        if profile:
            setattr(profile, 'verified_tier', tier)
            profile.save(update_fields=['verified_tier'])
        # update analytics
        try:
            from analytics.utils import calculate_user_metrics
            calculate_user_metrics(user)
        except Exception:
            pass
    except Exception:
        pass

# ---- Redaction / removal helper ----
def redact_document_if_needed(document):
    """
    If policy says remove PII after expiry, either delete file or replace with redacted placeholder.
    """
    try:
        # simple approach: clear file field, set redacted True
        document.file.delete(save=False)
        document.redacted = True
        document.meta = {'redacted_at': str(timezone.now())}
        document.save(update_fields=['redacted','meta'])
    except Exception:
        pass
