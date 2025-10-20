from django.contrib.auth import get_user_model
from django.db.models import Q
from decimal import Decimal
from django.utils import timezone
from marketplace.models import Project
from accounts.models import User
from reviews.models import Review
import math

# NOTE: This file hosts the core heuristic scoring logic.
# You can later replace / extend with ML embeddings & vector DB.

def skill_overlap_score(project_skills, user_skills):
    
    if not project_skills or not user_skills:
        return 0.0
    set_p = set([str(s).lower() for s in project_skills])
    set_u = set([str(s).lower() for s in user_skills])
    inter = set_p.intersection(set_u)
    
    denom = max(len(set_p), len(set_u))
    if denom == 0:
        return 0.0
    return len(inter) / denom  

def recency_boost(user):
   
    try:
        last = user.last_seen
        if not last:
            return 0.0
        days = (timezone.now() - last).days
        if days <= 1:
            return 0.2
        if days <= 7:
            return 0.1
        if days <= 30:
            return 0.02
        return 0.0
    except Exception:
        return 0.0

def rating_factor(user):
    # normalize user.rating (0..5) to 0..1
    try:
        r = float(getattr(user, 'rating', 0.0))
        return min(max(r / 5.0, 0.0), 1.0)
    except Exception:
        return 0.0

def trust_score_factor(user):
    # take trust_score field if exists (0..100) -> 0..1
    try:
        ts = float(getattr(user, 'trust_score', 0.0))
        return min(max(ts / 100.0, 0.0), 1.0)
    except Exception:
        return 0.0

def compute_candidate_score(project, candidate_user, weights=None):
    """
    Heuristic composite score:
    score = w1 * skill_overlap + w2 * rating + w3 * trust + w4 * recency + w5 * past_success
    Returns float 0..1
    """
    weights = weights or {
        'skill': 0.45,
        'rating': 0.2,
        'trust': 0.15,
        'recency': 0.1,
        'past_success': 0.1
    }

    
    project_skills = [s.name for s in getattr(project, 'skills').all()] if hasattr(project, 'skills') else project.recommended_freelancers or []
    user_skills = getattr(candidate_user, 'skills', []) or []
    skill_score = skill_overlap_score(project_skills, user_skills)  # 0..1

    rating = rating_factor(candidate_user)  
    trust = trust_score_factor(candidate_user) 
    recency = recency_boost(candidate_user) 

   
    try:
        total = getattr(candidate_user, 'total_projects', 0)
        completed = getattr(candidate_user, 'completed_orders', 0)
        past_success = (completed / total) if total and total > 0 else 0.0
    except Exception:
        past_success = 0.0

    raw = (weights['skill'] * skill_score +
           weights['rating'] * rating +
           weights['trust'] * trust +
           weights['recency'] * recency +
           weights['past_success'] * past_success)

    # normalize roughly to 0..1 using tanh for smoothing:
    score = math.tanh(raw * 1.2)
    return float(round(score, 4))
