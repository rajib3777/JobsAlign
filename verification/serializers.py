from rest_framework import serializers
from .models import VerificationRequest, Document, Selfie, VerificationAudit
from django.conf import settings

class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('id','request','document_type','file','filename','filesize','uploaded_at','processed','meta')
        read_only_fields = ('id','uploaded_at','processed','meta','filename','filesize')

    def validate_file(self, value):
        # validate file size & content type
        max_mb = getattr(settings, 'VERIFICATION', {}).get('MAX_DOCUMENT_SIZE_MB', 15)
        if value.size > max_mb * 1024 * 1024:
            raise serializers.ValidationError("Document file too large")
        # optional MIME check
        allowed = getattr(settings, 'VERIFICATION', {}).get('ALLOWED_DOCUMENT_TYPES', [])
        if allowed and value.content_type not in allowed:
            raise serializers.ValidationError("Invalid document type")
        return value


class SelfieUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Selfie
        fields = ('id','request','file','uploaded_at','processed','meta')
        read_only_fields = ('id','uploaded_at','processed','meta')

    def validate_file(self, value):
        max_mb = getattr(settings, 'VERIFICATION', {}).get('MAX_DOCUMENT_SIZE_MB', 10)
        if value.size > max_mb * 1024 * 1024:
            raise serializers.ValidationError("Selfie file too large")
        return value


class VerificationRequestSerializer(serializers.ModelSerializer):
    documents = DocumentUploadSerializer(many=True, read_only=True)
    selfies = SelfieUploadSerializer(many=True, read_only=True)

    class Meta:
        model = VerificationRequest
        fields = ('id','user','status','tier','created_at','updated_at','decision_by','decision_reason','decision_at','meta','documents','selfies','expires_at')
        read_only_fields = ('id','user','status','created_at','updated_at','decision_by','decision_reason','decision_at','meta','expires_at')


class AdminDecisionSerializer(serializers.Serializer):
    request_id = serializers.UUIDField()
    action = serializers.ChoiceField(choices=['approve_basic','approve_advanced','reject'])
    reason = serializers.CharField(allow_blank=True, required=False)
