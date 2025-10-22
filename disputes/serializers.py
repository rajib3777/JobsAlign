from rest_framework import serializers
from .models import Dispute, Evidence, DisputeTimeline, ArbitrationDecision
from django.contrib.auth import get_user_model

User = get_user_model()

class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = ('id','dispute','uploader','file','text','meta','created_at')
        read_only_fields = ('id','uploader','created_at')

class DisputeCreateSerializer(serializers.ModelSerializer):
    contract_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Dispute
        fields = ('id','contract_id','reason','description','created_at')
        read_only_fields = ('id','created_at')

    def validate(self, attrs):
        # ensure contract belongs to user and is eligible
        contract_id = attrs.get('contract_id')
        user = self.context['request'].user
        from marketplace.models import Contract
        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            raise serializers.ValidationError("Invalid contract")
        if user not in [contract.buyer, contract.freelancer]:
            raise serializers.ValidationError("Not a party to contract")
        # optional: only allow dispute when contract not already disputed
        if hasattr(contract, 'dispute') and contract.dispute:
            raise serializers.ValidationError("This contract already has a dispute")
        return attrs

    def create(self, validated_data):
        from marketplace.models import Contract
        contract = Contract.objects.get(id=validated_data.pop('contract_id'))
        user = self.context['request'].user
        dispute = Dispute.objects.create(contract=contract, opener=user, **validated_data)
        # set default SLA deadline: e.g., 72 hours from now
        from django.utils import timezone
        dispute.sla_deadline = timezone.now() + timezone.timedelta(hours=72)
        dispute.save(update_fields=['sla_deadline'])
        return dispute

class DisputeSerializer(serializers.ModelSerializer):
    timeline = serializers.SerializerMethodField()
    evidences = EvidenceSerializer(many=True, read_only=True)
    class Meta:
        model = Dispute
        fields = ('id','contract','opener','reason','description','status','assigned_mediator','sla_deadline','meta','created_at','updated_at','timeline','evidences')

    def get_timeline(self, obj):
        return [{"verb": t.verb, "actor": str(t.actor) if t.actor else None, "payload": t.payload, "created_at": t.created_at} for t in obj.timeline.all().order_by('created_at')]

class ArbitrationDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArbitrationDecision
        fields = '__all__'
        read_only_fields = ('id','decided_at')
