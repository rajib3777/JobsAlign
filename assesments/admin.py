from django.contrib import admin
from .models import Test, Question, Attempt, Answer

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('name','type','active','total_marks','pass_marks','weight','max_attempts')
    list_filter = ('type','active')
    inlines = [QuestionInline]

@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('id','user','test','attempt_no','status','score','passed','duration_sec','started_at','finished_at')
    list_filter = ('status','passed','test__type')
    search_fields = ('user__email','user__full_name')

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt','question','chosen','is_correct')
    list_filter = ('is_correct',)
