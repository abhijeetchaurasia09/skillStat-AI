from django.contrib import admin
from .models import Course, LearningMaterial, Recommendation

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'skill', 'difficulty', 'estimated_duration', 'provider', 'is_active')
    list_filter = ('skill', 'difficulty', 'is_active')
    search_fields = ('title', 'description', 'igot_course_id')

@admin.register(LearningMaterial)
class LearningMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'skill', 'course', 'extraction_status', 'page_count', 'uploaded_at')
    list_filter = ('extraction_status', 'skill', 'uploaded_at')
    search_fields = ('title', 'extracted_text')

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'skill', 'priority', 'gap_points', 'is_completed', 'created_at')
    list_filter = ('priority', 'is_completed', 'skill')
    search_fields = ('user__username', 'course__title', 'reason')
