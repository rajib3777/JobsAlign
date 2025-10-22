from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from .models import Dispute, Evidence, ArbitrationDecision
from .serializers import DisputeCreateSerializer, DisputeSerializer, EvidenceSerializer, ArbitrationDecisionSerializer
from .permissions import IsDisputePartyOrStaff
from django.shortcuts import get_object_or_404
from . import utils
from django.db import transaction

class CreateDisputeView(generics.CreateAPIView):
    serializer_class = DisputeCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        dispute = serializer.save()
        utils.log_timeline(dispute, self.request.user, 'dispute_created', {})
        # schedule summarizer
        from .tasks import summarize_evidence
        summarize_evidence.delay(str(dispute.id))
        return dispute

class DisputeDetailView(generics.RetrieveAPIView):
    queryset = Dispute.objects.all()
    serializer_class = DisputeSerializer
    permission_classes = [permissions.IsAuthenticated, IsDisputePartyOrStaff]

class UploadEvidenceView(generics.CreateAPIView):
    serializer_class = EvidenceSerializer
    permission_classes = [permissions.IsAuthenticated, IsDisputePartyOrStaff]

    def perform_create(self, serializer):
        evidence = serializer.save(uploader=self.request.user)
        utils.log_timeline(evidence.dispute, self.request.user, 'evidence_uploaded', {'evidence_id': str(evidence.id)})
        # trigger summarizer background job if needed
        from .tasks import summarize_evidence
        summarize_evidence.delay(str(evidence.dispute.id))
        return evidence

class PartyRespondView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsDisputePartyOrStaff]

    def post(self, request, dispute_id):
        dispute = get_object_or_404(Dispute, id=dispute_id)
        # add timeline entry for party response
        message = request.data.get('message')
        utils.log_timeline(dispute, request.user, 'party_response', {'message': message})
        return Response({'detail':'ok'})

# Admin endpoints
class AssignMediatorView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, dispute_id):
        dispute = get_object_or_404(Dispute, id=dispute_id)
        mediator_id = request.data.get('mediator_id')
        from django.contrib.auth import get_user_model
        User = get_user_model()
        mediator = get_object_or_404(User, id=mediator_id, is_staff=True)
        dispute.assigned_mediator = mediator
        dispute.status = 'under_review'
        dispute.sla_deadline = None
        dispute.save(update_fields=['assigned_mediator','status','sla_deadline'])
        utils.log_timeline(dispute, request.user, 'mediator_assigned', {'mediator_id': mediator_id})
        # notify mediator
        from notifications.utils import create_notification
        create_notification(user=mediator, verb='assigned_mediator', title='New dispute assigned', message=f'Dispute {dispute.id} assigned to you', data={'dispute_id': str(dispute.id)})
        return Response({'detail':'ok'})

class ProposeResolutionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsDisputePartyOrStaff]

    def post(self, request, dispute_id):
        dispute = get_object_or_404(Dispute, id=dispute_id)
        proposal = request.data.get('proposal')  # expected structured: {'type':'refund','amount':.., 'split': {...}}
        utils.log_timeline(dispute, request.user, 'proposal_made', {'proposal': proposal})
        # store latest proposal in meta
        dispute.meta['latest_proposal'] = proposal
        dispute.save(update_fields=['meta'])
        # notify counterparty & mediator
        other = dispute.contract.buyer if request.user == dispute.contract.freelancer else dispute.contract.freelancer
        from notifications.utils import create_notification
        create_notification(user=other, verb='proposal_received', title='Resolution proposal', message='A resolution was proposed', data={'dispute_id': str(dispute.id), 'proposal': proposal})
        return Response({'detail':'ok'})

class AdminResolveView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, dispute_id):
        dispute = get_object_or_404(Dispute, id=dispute_id)
        decision = request.data.get('decision')  # 'buyer_wins'|'freelancer_wins'|'split'
        details = request.data.get('details', {})
        with transaction.atomic():
            # create decision
            dec = ArbitrationDecision.objects.create(dispute=dispute, decided_by=request.user, decision=decision, details=details)
            # update dispute
            if decision == 'buyer_wins':
                dispute.status = 'resolved_buyer'
            elif decision == 'freelancer_wins':
                dispute.status = 'resolved_freelancer'
            else:
                dispute.status = 'resolved_freelancer'  # or a separate 'resolved_split' state
            dispute.meta['decision'] = {'decision': decision, 'details': details}
            dispute.save(update_fields=['status','meta'])
            utils.log_timeline(dispute, request.user, 'admin_resolved', {'decision': decision, 'details': details})
            # call payments resolution helper
            resolved = utils.unfreeze_escrow_for_dispute(dispute, release_to=decision)
            # notify parties
            from notifications.utils import create_notification
            create_notification(user=dispute.contract.buyer, verb='dispute_resolved', title='Dispute resolved', message=f'Decision: {decision}', data={'dispute_id': str(dispute.id)})
            create_notification(user=dispute.contract.freelancer, verb='dispute_resolved', title='Dispute resolved', message=f'Decision: {decision}', data={'dispute_id': str(dispute.id)})
        return Response({'ok': True, 'payment_result': bool(resolved)})
