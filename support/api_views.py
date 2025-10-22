from rest_framework import generics, permissions, views, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import TicketCategory, SupportTicket, TicketMessage, CannedResponse, SupportAudit
from .serializers import (TicketCategorySerializer, SupportTicketSerializer, CreateTicketSerializer,
                          TicketMessageSerializer, CreateMessageSerializer, CannedResponseSerializer)
from .permissions import IsSupportAgent, IsTicketOwnerOrAgent
from django.utils import timezone
from . import utils
from notifications.utils import create_notification

# Categories (admin)
class TicketCategoryListCreateView(generics.ListCreateAPIView):
    queryset = TicketCategory.objects.filter(is_active=True)
    serializer_class = TicketCategorySerializer
    permission_classes = [permissions.IsAdminUser]

class TicketCategoryListPublicView(generics.ListAPIView):
    queryset = TicketCategory.objects.filter(is_active=True)
    serializer_class = TicketCategorySerializer
    permission_classes = [permissions.AllowAny]

# Create ticket (user)
class CreateTicketView(generics.CreateAPIView):
    serializer_class = CreateTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        ticket = serializer.save(user=self.request.user, status='open')
        SupportAudit.objects.create(ticket=ticket, actor=self.request.user, verb='created_ticket', payload={})
        # run AI pre-processing (intent classification, priority suggestion)
        utils.classify_and_tag_ticket.delay(str(ticket.id))
        # notify support team (admin group) - using notifications util
        create_notification(user=None, verb='new_ticket', title='New support ticket', message=f'Ticket {ticket.subject}', data={'ticket_id': str(ticket.id)})
        return ticket

# User's ticket list & retrieve
class MyTicketsListView(generics.ListAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SupportTicket.objects.filter(user=self.request.user).order_by('-updated_at')

class TicketDetailView(generics.RetrieveAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated, IsTicketOwnerOrAgent]
    queryset = SupportTicket.objects.all()

# Agent: post message
class PostMessageView(generics.CreateAPIView):
    serializer_class = CreateMessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupportAgent]

    def perform_create(self, serializer):
        msg = serializer.save(sender=self.request.user)
        SupportAudit.objects.create(ticket=msg.ticket, actor=self.request.user, verb='agent_posted_message', payload={'msg_id': str(msg.id)})
        # notify ticket owner
        try:
            create_notification(user=msg.ticket.user, verb='ticket_reply', title=f'Reply on: {msg.ticket.subject}', message=msg.content[:200], data={'ticket_id': str(msg.ticket.id)})
        except Exception:
            pass

# User reply
class UserPostMessageView(generics.CreateAPIView):
    serializer_class = CreateMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        msg = serializer.save(sender=self.request.user)
        SupportAudit.objects.create(ticket=msg.ticket, actor=self.request.user, verb='user_posted_message', payload={'msg_id': str(msg.id)})
        # notify assigned agent(s) or support admins
        try:
            if msg.ticket.assigned_to:
                create_notification(user=msg.ticket.assigned_to, verb='new_message', title=f'New message on {msg.ticket.subject}', message=msg.content[:200], data={'ticket_id': str(msg.ticket.id)})
            else:
                create_notification(user=None, verb='new_message', title=f'New message on {msg.ticket.subject}', message=msg.content[:200], data={'ticket_id': str(msg.ticket.id)})
        except Exception:
            pass

# Agents: list all pending tickets
class AgentPendingTicketsView(generics.ListAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupportAgent]

    def get_queryset(self):
        return SupportTicket.objects.filter(status__in=['open','pending_agent','escalated']).order_by('priority','-updated_at')

# Canned responses
class CannedResponseListCreateView(generics.ListCreateAPIView):
    serializer_class = CannedResponseSerializer
    queryset = CannedResponse.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsSupportAgent]

# Admin resolve/assign endpoints (simple APIs)
class AssignTicketView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsSupportAgent]

    def post(self, request, ticket_id):
        ticket = get_object_or_404(SupportTicket, id=ticket_id)
        ticket.assigned_to = request.user
        ticket.status = 'pending_agent'
        ticket.save(update_fields=['assigned_to','status','updated_at'])
        SupportAudit.objects.create(ticket=ticket, actor=request.user, verb='assigned_ticket', payload={})
        create_notification(user=ticket.user, verb='assigned', title='Ticket assigned', message=f'Your ticket {ticket.subject} assigned to agent {request.user.username}', data={'ticket_id': str(ticket.id)})
        return Response({'ok': True})

class ResolveTicketView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsSupportAgent]

    def post(self, request, ticket_id):
        ticket = get_object_or_404(SupportTicket, id=ticket_id)
        ticket.mark_resolved(actor=request.user, note=request.data.get('note'))
        SupportAudit.objects.create(ticket=ticket, actor=request.user, verb='resolved_ticket', payload={'note': request.data.get('note')})
        create_notification(user=ticket.user, verb='ticket_resolved', title='Ticket resolved', message=f'Your ticket {ticket.subject} has been resolved', data={'ticket_id': str(ticket.id)})
        return Response({'ok': True})
