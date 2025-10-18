from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.apps import apps
from .models import Project, Bid, Contract, Milestone, Skill
from .serializers import (
    ProjectSerializer, ProjectCreateSerializer,
    BidSerializer, BidCreateSerializer,
    ContractSerializer, MilestoneSerializer
)
from .permissions import IsOwnerOrReadOnly, IsProjectOwner, IsFreelancer
from . import utils
from payments.utils import initiate_escrow_payment
from rest_framework.permissions import IsAuthenticated



class ProjectCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProjectSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            project = serializer.save(owner=request.user)

            payment_method = request.data.get("payment_method", "stripe")
            amount = project.budget_min

            payment_response = initiate_escrow_payment(
                buyer=request.user,
                project=project,
                amount=amount,
                method=payment_method,
            )

            if payment_response.get("success"):
                project.status = "in_review"
                project.save()
                return Response({"message": "Project created and escrow funded successfully."}, status=201)
            else:
                project.delete()
                return Response({"error": "Payment failed"}, status=400)
        return Response(serializer.errors, status=400)


class ProjectRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Project.objects.all().select_related("owner").prefetch_related("skills","attachments")
    serializer_class = ProjectSerializer
    permission_classes = [IsOwnerOrReadOnly]


class BidCreateView(generics.CreateAPIView):
    serializer_class = BidCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsFreelancer]

    def perform_create(self, serializer):
        bid = serializer.save()
        # optional: enqueue AI suggested bid calculation
        utils.enqueue_suggested_bid(bid)
        return bid


class BidListView(generics.ListAPIView):
    serializer_class = BidSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        project = get_object_or_404(Project, id=project_id)
        user = self.request.user
        # owner can see all bids; freelancers see only their own bids
        if project.owner == user:
            return project.bids.all()
        return project.bids.filter(freelancer=user)


class AcceptBidView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsProjectOwner]

    def post(self, request, bid_id):
        bid = get_object_or_404(Bid, id=bid_id)
        project = bid.project
        # permission check for owner
        if project.owner != request.user:
            return Response({"detail": "Forbidden"}, status=403)
        # create Contract
        contract = Contract.objects.create(
            project=project,
            bid=bid,
            buyer=project.owner,
            freelancer=bid.freelancer,
            total_amount=bid.amount,
            commission=utils.calculate_commission(bid.amount),
        )
        # set project status
        project.status = "in_progress"
        project.save(update_fields=["status","updated_at"])
        # create escrow via payments utils (async or sync)
        escrow_ref = utils.create_escrow_for_contract(contract)
        contract.escrow_reference = escrow_ref
        contract.save(update_fields=["escrow_reference"])
        return Response(ContractSerializer(contract).data, status=status.HTTP_201_CREATED)


class MilestoneCreateView(generics.CreateAPIView):
    serializer_class = MilestoneSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        m = serializer.save()
        # activity log
        utils.log_activity(m.contract.project, self.request.user, "milestone_created", {"milestone_id": str(m.id)})
        return m


class MilestoneApproveView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, milestone_id):
        milestone = get_object_or_404(Milestone, id=milestone_id)
        contract = milestone.contract
        # only buyer can approve
        if contract.buyer != request.user:
            return Response({"detail":"Forbidden"}, status=403)
        # mark approved and trigger payment release for milestone
        milestone.status = "approved"
        milestone.save(update_fields=["status","updated_at"])
        # ask payments app to release escrow for this milestone
        success = utils.release_milestone_payment(contract, milestone)
        if success:
            milestone.status = "paid"
            milestone.save(update_fields=["status","updated_at"])
            return Response({"detail":"Milestone paid"}, status=200)
        return Response({"detail":"Payment release failed"}, status=500)


class ContractDetailView(generics.RetrieveAPIView):
    serializer_class = ContractSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Contract.objects.filter(buyer=self.request.user) | Contract.objects.filter(freelancer=self.request.user)
