from django.contrib import admin
from .models import Skill, UserCompetency, Assessment, AssessmentQuestion, AssessmentAttempt, UserAnswer

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'required_level', 'icon')
    search_fields = ('name', 'description')
    list_filter = ('category',)

@admin.register(UserCompetency)
class UserCompetencyAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'current_level', 'gap', 'priority', 'last_assessed_at')
    list_filter = ('skill', 'last_assessed_at')
    search_fields = ('user__username', 'skill__name')

class AssessmentQuestionInline(admin.StackedInline):
    model = AssessmentQuestion
    extra = 1

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'time_limit_minutes', 'created_at')
    inlines = [AssessmentQuestionInline]

@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'skill', 'assessment', 'correct_option', 'difficulty')
    list_filter = ('skill', 'difficulty', 'assessment')
    search_fields = ('question_text', 'explanation')

@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'assessment', 'score_percentage', 'correct_answers', 'total_questions', 'completed_at')
    list_filter = ('assessment', 'completed_at')
    search_fields = ('user__username',)

@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_option', 'is_correct')
    list_filter = ('is_correct',)
