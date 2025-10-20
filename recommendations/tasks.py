from celery import shared_task
from django.contrib.auth import get_user_model
from marketplace.models import Project
from .models import ProjectRecommendation, UserRecommendation
from .utils import compute_candidate_score
from django.utils import timezone
from django.conf import settings

User = get_user_model()

@shared_task(bind=True)
def compute_recommendations_for_project(self, project_id, top_k=10):
    
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return False

    
    candidates = User.objects.filter(user_type='freelancer')[:2000]  

    scored = []
    for u in candidates:
        try:
            score = compute_candidate_score(project, u)
            if score > 0.01:
                scored.append({'user_id': str(u.id), 'score': score, 'reason': 'heuristic'})
        except Exception:
            continue

    scored_sorted = sorted(scored, key=lambda x: x['score'], reverse=True)[:top_k]

    ProjectRecommendation.objects.create(
        project_id=project_id,
        computed_at=timezone.now(),
        payload=scored_sorted,
        source='heuristic',
    )
    return True

@shared_task(bind=True)
def compute_recommendations_for_user(self, user_id, top_k=20):
    """
    Compute recommended projects for a freelancer.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return False

    
    projects = Project.objects.filter(status='open').order_by('-created_at')[:1000]
    scored = []
    for p in projects:
        try:
            score = compute_candidate_score(p, user)
            if score > 0.01:
                scored.append({'project_id': str(p.id), 'score': score, 'reason': 'heuristic'})
        except Exception:
            continue

    scored_sorted = sorted(scored, key=lambda x: x['score'], reverse=True)[:top_k]
    UserRecommendation.objects.create(
        user=user,
        computed_at=timezone.now(),
        payload=scored_sorted,
        source='heuristic'
    )
    return True
