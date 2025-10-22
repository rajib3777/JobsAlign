from celery import shared_task
from .models import Document, Selfie, VerificationRequest, VerificationAudit
from . import utils
from django.utils import timezone
from django.conf import settings

@shared_task(bind=True)
def process_document_async(self, document_id):
    
    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return

    VerificationAudit.objects.create(request=doc.request, actor=None, verb='doc_processing_started', payload={'doc_id': str(doc.id)})

    try:
        # 1. virus scan (placeholder - implement)
        vs = utils.virus_scan_file(doc.file)
        doc.meta['virus_scan'] = vs

        # 2. OCR
        ocr = utils.run_ocr_on_document(doc.file, doc.document_type)
        doc.meta['ocr'] = ocr or {}
        doc.processed = True
        doc.filesize = getattr(doc.file, 'size', None)
        doc.save(update_fields=['processed','meta','filesize','uploaded_at'])

        # 3. update request meta
        req = doc.request
        req.meta = {**(req.meta or {}), 'last_ocr': ocr or {}}
        req.save(update_fields=['meta','updated_at'])

        # 4. if OCR confidence high and there is a face comparison already high, auto-approve
        face_score = req.meta.get('face_match_score') or 0
        ocr_conf = (ocr.get('confidence') if isinstance(ocr, dict) else 0) or 0
        threshold = getattr(settings, 'VERIFICATION', {}).get('AUTO_APPROVE_THRESHOLD', 0.95)
        if ocr_conf >= threshold and face_score >= threshold:
            req.mark_approved(tier=req.tier or 'basic', actor=None, reason='auto_approved_by_ocr_and_face_confidence')
            VerificationAudit.objects.create(request=req, actor=None, verb='auto_approved', payload={'ocr_conf': ocr_conf, 'face_score': face_score})
            utils.grant_verification_badge(req.user, req.tier or 'basic')
            utils.notify_user_verification_status(req.user, req)
        else:
            # send to manual review queue
            req.mark_under_review()
            VerificationAudit.objects.create(request=req, actor=None, verb='sent_to_review', payload={'ocr_conf': ocr_conf, 'face_score': face_score})
    except Exception as e:
        VerificationAudit.objects.create(request=doc.request, actor=None, verb='doc_processing_failed', payload={'error': str(e)})
        raise

@shared_task(bind=True)
def face_match_async(self, selfie_id):
    """
    Run face-match between user's latest selfie and available document facial region(s).
    """
    try:
        selfie = Selfie.objects.get(id=selfie_id)
    except Selfie.DoesNotExist:
        return

    try:
        req = selfie.request
        # 1. run face match util which returns score 0..1
        score, details = utils.run_face_match(selfie.file, req)
        selfie.meta['face_match'] = {'score': score, 'details': details}
        selfie.processed = True
        selfie.save(update_fields=['meta','processed','uploaded_at'])

        # update request meta
        req.meta = {**(req.meta or {}), 'face_match_score': score}
        req.save(update_fields=['meta','updated_at'])

        VerificationAudit.objects.create(request=req, actor=None, verb='face_match_done', payload={'score': score})
    except Exception as e:
        VerificationAudit.objects.create(request=req, actor=None, verb='face_match_failed', payload={'error': str(e)})
        raise

@shared_task
def auto_review_queue_processor(batch=20):
    """
    Periodic job for admins: collect under_review requests and prioritize for human review,
    or escalate older requests.
    """
    now = timezone.now()
    qs = VerificationRequest.objects.filter(status='under_review').order_by('created_at')[:batch]
    for r in qs:
        # if older than X days alert admin via notifications
        age = (now - r.created_at).days
        if age > 3:
            # notify admin group
            from notifications.utils import create_notification
            create_notification(user=None, verb='verification_escalation', title='Verification escalation', message=f'Request {r.id} needs attention', data={'request_id': str(r.id)})
    return True

@shared_task
def expire_verifications():
    """
    Set status to expired when past retention/expires_at reached (or remove PII if policy).
    """
    now = timezone.now()
    expired = VerificationRequest.objects.filter(status__in=['approved_basic','approved_advanced'], expires_at__lte=now)
    for r in expired:
        r.status = 'expired'
        r.save(update_fields=['status','updated_at'])
        VerificationAudit.objects.create(request=r, actor=None, verb='expired', payload={})
        # optionally remove files if policy requires (redact)
        for d in r.documents.all():
            utils.redact_document_if_needed(d)
