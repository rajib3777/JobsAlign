from rest_framework import permissions

class IsParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if hasattr(obj, "participants"):
            return obj.participants.filter(id=user.id).exists()
        if hasattr(obj, "conversation"):
            return obj.conversation.participants.filter(id=user.id).exists()
        return False
