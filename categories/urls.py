from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.CategoryListView.as_view(), name='categories-list'),
    path('<slug:slug>/', api_views.CategoryDetailView.as_view(), name='category-detail'),
    path('create/', api_views.CategoryCreateView.as_view(), name='category-create'),
    path('subcategory/create/', api_views.SubCategoryCreateView.as_view(), name='subcategory-create'),
    path('skill/create/', api_views.SkillCreateView.as_view(), name='skill-create'),
    path('freelancer/', api_views.FreelancerCategoryView.as_view(), name='freelancer-categories'),
    path('freelancers/by/', api_views.FreelancerByCategoryView.as_view(), name='freelancer-by-category'),
    path('metrics/', api_views.CategoryMetricView.as_view(), name='category-metrics'),
    path('notify-pref/', api_views.CategoryNotifyPrefView.as_view(), name='category-notify-pref'),
    path('suggest/', api_views.SuggestCategoryView.as_view(), name='suggest-category'),
]
