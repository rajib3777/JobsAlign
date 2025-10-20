from rest_framework import permissions

class IsConversationParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if obj is None:
            return False
        # obj could be Conversation or Message
        if hasattr(obj, 'participants'):
            return obj.participants.filter(user=user).exists()
        if hasattr(obj, 'conversation'):
            return obj.conversation.participants.filter(user=user).exists()
        return False
