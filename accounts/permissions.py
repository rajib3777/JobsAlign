from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrAdmin(BasePermission):
    """
    Allow object access if request.user is the object owner or is staff.
    """
    def has_object_permission(self, request, view, obj):
        # safe methods allowed widely; write only for owner or staff
        if request.method in SAFE_METHODS:
            return True
        try:
            return obj == request.user or request.user.is_staff
        except Exception:
            return False
