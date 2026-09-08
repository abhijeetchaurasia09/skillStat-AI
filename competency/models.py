from django.db import models
from django.contrib.auth.models import User

class Skill(models.Model):
    """
    Represents a recognized competency or skill within the organization / iGOT framework.
    """
    CATEGORY_CHOICES = [
        ('Core Analytics', 'Core Analytics'),
        ('Technical', 'Technical / Programming'),
        ('Methodology', 'Survey & Research Methodology'),
        ('Governance', 'Policy & Statistical Interpretation'),
    ]

    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=80, choices=CATEGORY_CHOICES, default='Core Analytics')
    required_level = models.PositiveIntegerField(
        default=80,
        help_text="Target required competency score percentage (e.g. 80%)"
    )
    icon = models.CharField(max_length=60, default='bi-cpu', help_text="Bootstrap Icons class name")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (Required: {self.required_level}%)"


class UserCompetency(models.Model):
    """
    Tracks a user's current demonstrated competency level in a specific skill.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='competencies')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='user_competencies')
    current_level = models.FloatField(
        default=0.0,
        help_text="Current competency score percentage (0 - 100)"
    )
    last_assessed_at = models.DateTimeField(auto_now=True)
    assessment_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'skill')
        ordering = ['skill__name']

    def __str__(self):
        return f"{self.user.username} - {self.skill.name}: {self.current_level:.1f}%"

    @property
    def gap(self):
        """
        Calculates gap = required_level - current_level.
        If current_level > required_level, gap is 0.
        """
        val = self.skill.required_level - self.current_level
        return round(max(0.0, val), 1)

    @property
    def priority(self):
        """
        Priority based on gap:
        gap >= 40 -> HIGH
        gap >= 20 -> MEDIUM
        gap < 20  -> LOW
        """
        g = self.gap
        if g >= 40.0:
            return 'HIGH'
        elif g >= 20.0:
            return 'MEDIUM'
        else:
            return 'LOW'

    @property
    def priority_badge_class(self):
        p = self.priority
        if p == 'HIGH':
            return 'danger'
        elif p == 'MEDIUM':
            return 'warning'
        return 'success'


class Assessment(models.Model):
    """
    A diagnostic or comprehensive competency assessment.
    """
    title = models.CharField(max_length=200, default="Core Competency Diagnostic Assessment")
    description = models.TextField(default="Official baseline assessment evaluating key competencies for statistical officers and analysts.")
    is_active = models.BooleanField(default=True)
    time_limit_minutes = models.PositiveIntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class AssessmentQuestion(models.Model):
    """
    A multiple-choice question linked to an Assessment and a specific Skill.
    """
    DIFFICULTY_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]
    OPTION_CHOICES = [
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    ]

    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='assessment_questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    explanation = models.TextField(help_text="Explains the correct concept")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Intermediate')

    def __str__(self):
        return f"[{self.skill.name}] {self.question_text[:60]}..."


class AssessmentAttempt(models.Model):
    """
    Record of a user taking an assessment.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessment_attempts')
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='attempts')
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    score_percentage = models.FloatField(default=0.0)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.user.username} - {self.assessment.title} - {self.score_percentage:.1f}% ({self.completed_at.strftime('%Y-%m-%d')})"


class UserAnswer(models.Model):
    """
    Record of a user's answer to a specific assessment question.
    """
    attempt = models.ForeignKey(AssessmentAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(AssessmentQuestion, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Attempt {self.attempt_id} - Q{self.question_id}: {self.selected_option} ({'Correct' if self.is_correct else 'Wrong'})"
