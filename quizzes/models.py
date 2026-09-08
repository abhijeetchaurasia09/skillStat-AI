from django.db import models
from django.contrib.auth.models import User
from competency.models import Skill
from learning.models import LearningMaterial

class Quiz(models.Model):
    """
    A quiz generated either via AI from learning materials / PDFs or standardized practice.
    """
    DIFFICULTY_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]
    SOURCE_CHOICES = [
        ('uploaded_pdf', 'AI Generated from Uploaded Material'),
        ('ai_generated', 'AI Generated Knowledge Check'),
        ('standard', 'Curriculum Practice Quiz'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=220)
    material = models.ForeignKey(LearningMaterial, on_delete=models.SET_NULL, null=True, blank=True, related_name='quizzes')
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True, related_name='quizzes')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Intermediate')
    source_type = models.CharField(max_length=30, choices=SOURCE_CHOICES, default='uploaded_pdf')
    is_ai_generated = models.BooleanField(default=True)
    ai_mode_used = models.CharField(max_length=20, default='mock', help_text="'mock' (demo) or 'real' LLM API")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_difficulty_display()})"


class QuizQuestion(models.Model):
    """
    Individual MCQ question within a Quiz.
    """
    OPTION_CHOICES = [
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True, related_name='quiz_questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=350)
    option_b = models.CharField(max_length=350)
    option_c = models.CharField(max_length=350)
    option_d = models.CharField(max_length=350)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    explanation = models.TextField(help_text="Detailed pedagogical explanation")
    difficulty = models.CharField(max_length=20, default='Intermediate')

    def __str__(self):
        return f"Quiz #{self.quiz_id}: {self.question_text[:60]}"


class QuizAttempt(models.Model):
    """
    Record of a user taking and completing a Quiz.
    Tracks before & after competency to prove closed-loop learning.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    score_percentage = models.FloatField(default=0.0)
    before_competency = models.FloatField(default=0.0, help_text="Competency score of related skill prior to quiz")
    after_competency = models.FloatField(default=0.0, help_text="Updated competency score after quiz")
    competency_gain = models.FloatField(default=0.0, help_text="Net improvement in competency score")
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.score_percentage:.1f}% (+{self.competency_gain:.1f}%)"


class QuizUserAnswer(models.Model):
    """
    Records the option selected by the user for a specific quiz question.
    """
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Attempt #{self.attempt_id} Q#{self.question_id}: {self.selected_option} ({'Correct' if self.is_correct else 'Wrong'})"
