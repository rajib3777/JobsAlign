from rest_framework import permissions

class IsDisputePartyOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff:
            return True
        # obj may be Dispute or related model
        if hasattr(obj, 'dispute'):
            dispute = obj.dispute
        else:
            dispute = obj
        return dispute.opener == user or dispute.contract.buyer == user or dispute.contract.freelancer == user
