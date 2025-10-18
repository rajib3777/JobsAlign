from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return hasattr(obj, "owner") and obj.owner == request.user

class IsProjectOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class IsFreelancer(permissions.BasePermission):
    def has_permission(self, request, view):
        # If you have user_type: check freelancer
        return getattr(request.user, "user_type", "") == "freelancer"
