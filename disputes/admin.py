from django.contrib import admin
from .models import Dispute, Evidence, DisputeTimeline, ArbitrationDecision

@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ('id','contract','opener','status','assigned_mediator','created_at')
    search_fields = ('contract__id','opener__email')
    list_filter = ('status','created_at')
    readonly_fields = ('id','created_at','updated_at')

@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ('id','dispute','uploader','created_at')
    readonly_fields = ('id','created_at')

@admin.register(DisputeTimeline)
class TimelineAdmin(admin.ModelAdmin):
    list_display = ('id','dispute','actor','verb','created_at')
    readonly_fields = ('id','created_at')

@admin.register(ArbitrationDecision)
class DecisionAdmin(admin.ModelAdmin):
    list_display = ('id','dispute','decided_by','decision','decided_at')
    readonly_fields = ('id','decided_at')

