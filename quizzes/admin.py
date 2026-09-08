from django.contrib import admin
from .models import Quiz, QuizQuestion, QuizAttempt, QuizUserAnswer

class QuizQuestionInline(admin.StackedInline):
    model = QuizQuestion
    extra = 1

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'skill', 'difficulty', 'source_type', 'ai_mode_used', 'created_at')
    list_filter = ('source_type', 'ai_mode_used', 'difficulty', 'skill')
    search_fields = ('title', 'user__username')
    inlines = [QuizQuestionInline]

@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'quiz', 'skill', 'correct_option', 'difficulty')
    list_filter = ('skill', 'difficulty')
    search_fields = ('question_text', 'explanation')

class QuizUserAnswerInline(admin.TabularInline):
    model = QuizUserAnswer
    extra = 0
    readonly_fields = ('question', 'selected_option', 'is_correct')

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score_percentage', 'before_competency', 'after_competency', 'competency_gain', 'completed_at')
    list_filter = ('completed_at',)
    search_fields = ('user__username', 'quiz__title')
    inlines = [QuizUserAnswerInline]
