from django.contrib import admin
from .models import Project, Bid, Contract, Milestone, Skill, ProjectAttachment, ProjectActivityLog

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name","slug")
    search_fields = ("name",)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title","owner","status","created_at","is_featured")
    list_filter = ("status","is_featured")
    search_fields = ("title","description")

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ("project","freelancer","amount","status","created_at")
    list_filter = ("status",)

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ("project","buyer","freelancer","total_amount","is_active","started_at")
    readonly_fields = ("escrow_reference",)

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ("title","contract","amount","status","due_date")

@admin.register(ProjectActivityLog)
class ProjectActivityAdmin(admin.ModelAdmin):
    list_display = ("project","actor","action","created_at")
    readonly_fields = ("meta",)

