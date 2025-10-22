from .models import Category, SubCategory, Skill, CategoryMetric, FreelancerCategory
from marketplace.models import Project, Bid, Contract
from django.utils import timezone
from collections import Counter
import re

def infer_skills_for_user(user):
    """
    Placeholder: infer skills from user's profile text or portfolio.
    Returns list of skill slugs (strings).
    Replace this with embeddings/NER model later.
    """
    # naive: read user.profile.bio if exists
    slugs = []
    try:
        profile = getattr(user, 'profile', None) or getattr(user, 'User', None)
        text = ''
        if profile:
            text = (getattr(profile, 'bio', '') or '') + ' ' + (getattr(profile, 'summary', '') or '')
        text = text.lower()
        # simple matching against known skills
        skills = Skill.objects.filter(is_active=True).values_list('slug', 'name')
        for slug,name in skills:
            if slug.lower() in text or name.lower() in text:
                slugs.append(slug)
    except Exception:
        pass
    return list(set(slugs))

def suggest_category_for_text(text):
    """
    Very naive heuristic: count keyword hits in category/subcategory/skills.
    Replace with ML (embedding similarity) later.
    """
    text_l = text.lower()
    scores = Counter()
    for cat in Category.objects.filter(is_active=True):
        hits = 0
        if cat.name.lower() in text_l or (cat.description and cat.description.lower() in text_l):
            hits += 2
        for sub in cat.subcategories.filter(is_active=True):
            if sub.name.lower() in text_l or (sub.description and sub.description.lower() in text_l):
                hits += 1
            for sk in sub.skills.filter(is_active=True):
                if sk.name.lower() in text_l:
                    hits += 1
        if hits:
            scores[cat.slug] += hits
    if not scores:
        return None
    best = scores.most_common(1)[0][0]
    return Category.objects.filter(slug=best).first().slug

def compute_category_metrics_for_date(date=None):
    """
    Aggregate marketplace data into CategoryMetric for the given date.
    """
    if date is None:
        date = timezone.now().date()
    cats = Category.objects.filter(is_active=True)
    results = []
    for cat in cats:
        projects = Project.objects.filter(category=cat)
        demand = projects.filter(created_at__date=date).count()
        supply = FreelancerCategory.objects.filter(category=cat, verified=True).count()
        bids = Bid.objects.filter(project__in=projects)
        avg_bid = bids.aggregate_avg = bids.aggregate=models  # placeholder to avoid runtime error in static snippet
        # We'll compute simple stats safely:
        avg_bid_val = bids.aggregate(avg=models.Avg('amount'))['avg'] if bids.exists() else 0
        completed = projects.filter(status='completed').count()
        total = projects.count() or 1
        success_rate = (completed / total) * 100
        # naive trending score: demand vs last week (placeholder)
        # Save metric
        cm, created = CategoryMetric.objects.update_or_create(
            category=cat, subcategory=None, date=date,
            defaults={
                'demand': demand,
                'supply': supply,
                'avg_bid': avg_bid_val or 0,
                'avg_hire_time_hours': 0,
                'success_rate': success_rate,
                'trending_score': 0.0
            }
        )
        results.append(cm)
    return results
