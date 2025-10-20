from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import ProjectRecommendation, UserRecommendation
from .serializers import ProjectRecommendationSerializer, UserRecommendationSerializer
from . import tasks
from django.utils import timezone
from datetime import timedelta

class ProjectRecommendationView(generics.RetrieveAPIView):
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectRecommendationSerializer
    lookup_field = 'project_id'
    queryset = ProjectRecommendation.objects.all()

    def retrieve(self, request, *args, **kwargs):
        project_id = kwargs.get('project_id')
        rec = ProjectRecommendation.objects.filter(project_id=project_id).order_by('-computed_at').first()
        stale = True
        if rec:
            if (timezone.now() - rec.computed_at).total_seconds() < rec.ttl_seconds:
                stale = False
        if not rec or stale:
            
            try:
                tasks.compute_recommendations_for_project.delay(str(project_id))
            except Exception:
                pass
        if rec:
            return Response(ProjectRecommendationSerializer(rec).data)
        return Response({"detail":"Recommendation compute scheduled"}, status=status.HTTP_202_ACCEPTED)

class UserRecommendationView(generics.RetrieveAPIView):
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserRecommendationSerializer
    lookup_field = 'user_id'
    queryset = UserRecommendation.objects.all()

    def retrieve(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        rec = UserRecommendation.objects.filter(user_id=user_id).order_by('-computed_at').first()
        stale = True
        if rec:
            if (timezone.now() - rec.computed_at).total_seconds() < rec.ttl_seconds:
                stale = False
        if not rec or stale:
            try:
                tasks.compute_recommendations_for_user.delay(str(user_id))
            except Exception:
                pass
        if rec:
            return Response(UserRecommendationSerializer(rec).data)
        return Response({"detail":"Recommendation compute scheduled"}, status=status.HTTP_202_ACCEPTED)

class TriggerProjectRecommendation(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]  

    def post(self, request, project_id):
        
        from marketplace.models import Project
        project = get_object_or_404(Project, id=project_id)
        if project.owner != request.user and not request.user.is_staff:
            return Response({"detail":"Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        tasks.compute_recommendations_for_project.delay(str(project_id))
        return Response({"detail":"Recommendation job scheduled"}, status=status.HTTP_202_ACCEPTED)
