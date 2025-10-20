from django.contrib import admin
from .models import ProjectRecommendation, UserRecommendation

@admin.register(ProjectRecommendation)
class ProjectRecommendationAdmin(admin.ModelAdmin):
    list_display = ('project_id','computed_at','source')
    readonly_fields = ('id','computed_at')

@admin.register(UserRecommendation)
class UserRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user','computed_at','source')
    readonly_fields = ('id','computed_at')

