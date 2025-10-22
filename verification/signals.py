from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import VerificationRequest, Document, Selfie, VerificationAudit
from .tasks import process_document_async, face_match_async
from django.utils import timezone

@receiver(post_save, sender=Document)
def on_document_uploaded(sender, instance, created, **kwargs):
    if created:
        VerificationAudit.objects.create(request=instance.request, actor=instance.user, verb='document_uploaded', payload={'doc_id': str(instance.id)})
        # schedule processing
        process_document_async.delay(str(instance.id))

@receiver(post_save, sender=Selfie)
def on_selfie_uploaded(sender, instance, created, **kwargs):
    if created:
        VerificationAudit.objects.create(request=instance.request, actor=instance.user, verb='selfie_uploaded', payload={'selfie_id': str(instance.id)})
        face_match_async.delay(str(instance.id))
