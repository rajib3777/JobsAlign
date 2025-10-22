from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from .models import Category, SubCategory, Skill, FreelancerCategory, CategoryMetric, CategoryNotificationPreference
from .serializers import CategorySerializer, SubCategorySerializer, SkillSerializer, FreelancerCategorySerializer, CategoryMetricSerializer, CategoryNotificationPreferenceSerializer
from .permissions import IsAdminOrReadOnly
from django.shortcuts import get_object_or_404
from django.db.models import Q
from . import utils
from django.utils import timezone

# Public list of categories (read-only for non-admin)
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

# Admin-only category create/update
class CategoryCreateView(generics.CreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]

class SubCategoryCreateView(generics.CreateAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    permission_classes = [permissions.IsAdminUser]

class SkillCreateView(generics.CreateAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAdminUser]

# Freelancer: claim category
class FreelancerCategoryView(generics.ListCreateAPIView):
    serializer_class = FreelancerCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FreelancerCategory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # When freelancer claims category, auto-infer skills from profile (utils placeholder)
        instance = serializer.save(user=self.request.user)
        inferred_skills = utils.infer_skills_for_user(self.request.user)
        # try to attach inferred skills if they belong to subcategory
        for s in inferred_skills:
            try:
                skill = Skill.objects.filter(slug=s).first()
                if skill:
                    instance.skills.add(skill)
            except Exception:
                continue

# Search freelancers by category/subcategory
class FreelancerByCategoryView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = FreelancerCategorySerializer

    def get_queryset(self):
        cat_slug = self.request.query_params.get('category')
        sub_slug = self.request.query_params.get('subcategory')
        qs = FreelancerCategory.objects.filter(verified=True)
        if cat_slug:
            qs = qs.filter(category__slug=cat_slug)
        if sub_slug:
            qs = qs.filter(subcategory__slug=sub_slug)
        return qs

# Metrics view
class CategoryMetricView(generics.ListAPIView):
    queryset = CategoryMetric.objects.all().order_by('-date')[:50]
    serializer_class = CategoryMetricSerializer
    permission_classes = [permissions.AllowAny]

# Preference endpoints
class CategoryNotifyPrefView(generics.CreateAPIView):
    serializer_class = CategoryNotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cat_id = request.data.get('category')
        pref, created = CategoryNotificationPreference.objects.update_or_create(
            user=request.user, category_id=cat_id,
            defaults={'notify_new_jobs': request.data.get('notify_new_jobs', True),
                      'daily_digest': request.data.get('daily_digest', False)}
        )
        return Response(CategoryNotificationPreferenceSerializer(pref).data)

# Auto-suggest category for a job description (ML placeholder)
class SuggestCategoryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        text = request.data.get('text','')
        suggestion = utils.suggest_category_for_text(text)
        return Response({"suggestion": suggestion})
