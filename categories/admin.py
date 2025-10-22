from django.contrib import admin
from .models import Category, SubCategory, Skill, FreelancerCategory, CategoryMetric, CategoryNotificationPreference

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name','slug','visibility','is_active','manager')
    search_fields = ('name','slug')
    list_filter = ('visibility','is_active')

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name','category','slug','is_active')
    search_fields = ('name','slug')

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name','subcategory','slug','is_active')
    search_fields = ('name','slug')

@admin.register(FreelancerCategory)
class FreelancerCategoryAdmin(admin.ModelAdmin):
    list_display = ('user','category','subcategory','verified','created_at')
    list_filter = ('verified','category')

@admin.register(CategoryMetric)
class CategoryMetricAdmin(admin.ModelAdmin):
    list_display = ('category','subcategory','date','demand','supply','trending_score')
