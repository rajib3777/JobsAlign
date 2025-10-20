from django.contrib import admin
from .models import Review, ReviewReply

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "reviewer", "reviewee", "rating", "average_score", "created_at")
    search_fields = ("reviewer__email", "reviewee__email", "comment")
    list_filter = ("recommended", "created_at")

@admin.register(ReviewReply)
class ReviewReplyAdmin(admin.ModelAdmin):
    list_display = ("review", "responder", "created_at")
