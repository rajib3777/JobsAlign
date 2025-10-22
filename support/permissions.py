from rest_framework import permissions

class IsSupportAgent(permissions.BasePermission):
    """
    Simple permission: staff users or users with 'is_support_agent' flag in profile.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        # optional flag in profile or user attribute
        return getattr(user, 'is_support_agent', False)

class IsTicketOwnerOrAgent(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or getattr(request.user, 'is_support_agent', False):
            return True
        return obj.user_id == request.user.id
