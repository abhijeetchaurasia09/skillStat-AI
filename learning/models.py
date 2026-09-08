from django.db import models
from django.contrib.auth.models import User
from competency.models import Skill

class Course(models.Model):
    """
    Learning course linked to competencies. Can be mapped to official iGOT Karmayogi modules.
    """
    DIFFICULTY_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='courses')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Beginner')
    estimated_duration = models.CharField(max_length=60, default='4 Hours')
    external_url = models.URLField(blank=True, help_text="iGOT Karmayogi or external portal URL")
    igot_course_id = models.CharField(max_length=100, blank=True, help_text="Official iGOT Course ID mapping")
    provider = models.CharField(max_length=120, default='iGOT Karmayogi / SkillStat AI')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} ({self.skill.name})"


class LearningMaterial(models.Model):
    """
    Uploaded PDF documents and learning material processed for text extraction and AI MCQ generation.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Extraction'),
        ('success', 'Extraction Succeeded'),
        ('empty', 'Empty Document / No Extractable Text'),
        ('failed', 'Extraction Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_materials', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='materials')
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True, related_name='materials')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='materials/')
    extracted_text = models.TextField(blank=True)
    page_count = models.PositiveIntegerField(default=0)
    extraction_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    extraction_error = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} ({self.extraction_status})"

    @property
    def word_count(self):
        if self.extracted_text:
            return len(self.extracted_text.split())
        return 0


class Recommendation(models.Model):
    """
    Explainable AI recommendation generated based on user skill gaps.
    """
    PRIORITY_CHOICES = [
        ('HIGH', 'High Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('LOW', 'Low Priority'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='recommendations')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='recommendations')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    reason = models.TextField(help_text="Detailed explainable reason justifying this recommendation")
    gap_points = models.FloatField(default=0.0)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-gap_points', '-created_at']
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user.username} -> {self.course.title} [{self.priority}]"

    @property
    def badge_class(self):
        if self.priority == 'HIGH':
            return 'danger'
        elif self.priority == 'MEDIUM':
            return 'warning'
        return 'info'
