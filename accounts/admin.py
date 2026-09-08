from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'job_role', 'created_at')
    search_fields = ('user__username', 'user__email', 'department', 'job_role')
    list_filter = ('department', 'job_role')
