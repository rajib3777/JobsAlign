from rest_framework.permissions import BasePermission

class IsFreelancer(BasePermission):
    message = "Only freelancers can take assessments."
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and getattr(u, 'user_type', '') == 'freelancer')
