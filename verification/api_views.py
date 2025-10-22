from rest_framework import generics, permissions, views, status
from rest_framework.response import Response
from .models import VerificationRequest, Document, Selfie, VerificationAudit
from .serializers import (VerificationRequestSerializer, DocumentUploadSerializer, SelfieUploadSerializer, AdminDecisionSerializer)
from django.shortcuts import get_object_or_404
from . import utils
from .tasks import process_document_async, face_match_async
from django.utils import timezone

class CreateVerificationRequestView(generics.CreateAPIView):
    serializer_class = VerificationRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        req = serializer.save(user=self.request.user, status='pending')
        # audit
        VerificationAudit.objects.create(request=req, actor=self.request.user, verb='created_request', payload={})
        # optionally schedule auto-check
        req.mark_under_review()
        return req

class MyVerificationRequestView(generics.RetrieveAPIView):
    serializer_class = VerificationRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        req = VerificationRequest.objects.filter(user=self.request.user).order_by('-created_at').first()
        if not req:
            raise generics.Http404
        return req

class UploadDocumentView(generics.CreateAPIView):
    serializer_class = DocumentUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        req_id = self.request.data.get('request')
        req = get_object_or_404(VerificationRequest, id=req_id, user=self.request.user)
        doc = serializer.save(user=self.request.user, request=req)
        VerificationAudit.objects.create(request=req, actor=self.request.user, verb='uploaded_document', payload={'document_id': str(doc.id), 'type': doc.document_type})
        # trigger background processing (OCR, virus-scan)
        process_document_async.delay(str(doc.id))
        return doc

class UploadSelfieView(generics.CreateAPIView):
    serializer_class = SelfieUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        req_id = self.request.data.get('request')
        req = get_object_or_404(VerificationRequest, id=req_id, user=self.request.user)
        selfie = serializer.save(user=self.request.user, request=req)
        VerificationAudit.objects.create(request=req, actor=self.request.user, verb='uploaded_selfie', payload={'selfie_id': str(selfie.id)})
        face_match_async.delay(str(selfie.id))
        return selfie

# Admin endpoints
class AdminListPendingView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = VerificationRequestSerializer
    queryset = VerificationRequest.objects.filter(status__in=['pending','under_review']).order_by('created_at')


class AdminDecisionView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        s = AdminDecisionSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        req = get_object_or_404(VerificationRequest, id=data['request_id'])
        action = data['action']
        reason = data.get('reason')
        if action == 'reject':
            req.mark_rejected(actor=request.user, reason=reason)
            VerificationAudit.objects.create(request=req, actor=request.user, verb='rejected', payload={'reason': reason})
            utils.notify_user_verification_status(req.user, req)
            return Response({'ok': True})
        elif action in ('approve_basic','approve_advanced'):
            tier = 'basic' if action == 'approve_basic' else 'advanced'
            req.mark_approved(tier=tier, actor=request.user, reason=reason)
            VerificationAudit.objects.create(request=req, actor=request.user, verb='approved', payload={'tier': tier, 'reason': reason})
            utils.grant_verification_badge(req.user, tier)
            utils.notify_user_verification_status(req.user, req)
            return Response({'ok': True})
        return Response({'detail': 'invalid action'}, status=status.HTTP_400_BAD_REQUEST)

