from django.test import TestCase
from django.contrib.auth.models import User
from competency.models import Skill, UserCompetency, Assessment, AssessmentQuestion, AssessmentAttempt
from competency.services import CompetencyService

class CompetencyTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='analyst', password='password123')
        
        self.skill_reg = Skill.objects.create(
            name='Regression',
            category='Core Analytics',
            required_level=80
        )
        self.skill_py = Skill.objects.create(
            name='Python',
            category='Technical',
            required_level=80
        )
        self.skill_stat = Skill.objects.create(
            name='Statistics',
            category='Core Analytics',
            required_level=80
        )

        # Baseline competencies
        UserCompetency.objects.create(user=self.user, skill=self.skill_reg, current_level=35.0, assessment_count=1)
        UserCompetency.objects.create(user=self.user, skill=self.skill_py, current_level=55.0, assessment_count=1)
        UserCompetency.objects.create(user=self.user, skill=self.skill_stat, current_level=75.0, assessment_count=1)

    def test_skill_gap_calculation_and_priorities(self):
        """Verify gap = required - current and priority threshold classification."""
        gaps = CompetencyService.get_skill_gaps(self.user)
        gap_map = {g['skill'].name: g for g in gaps}

        # Regression: 80 - 35 = 45 -> HIGH
        self.assertEqual(gap_map['Regression']['gap'], 45.0)
        self.assertEqual(gap_map['Regression']['priority'], 'HIGH')

        # Python: 80 - 55 = 25 -> MEDIUM
        self.assertEqual(gap_map['Python']['gap'], 25.0)
        self.assertEqual(gap_map['Python']['priority'], 'MEDIUM')

        # Statistics: 80 - 75 = 5 -> LOW
        self.assertEqual(gap_map['Statistics']['gap'], 5.0)
        self.assertEqual(gap_map['Statistics']['priority'], 'LOW')

    def test_overall_competency_calculation(self):
        """Verify average overall score calculation across competencies."""
        # Average: (35 + 55 + 75) / 3 = 165 / 3 = 55.0%
        overall = CompetencyService.calculate_overall_competency(self.user)
        self.assertEqual(overall, 55.0)

    def test_assessment_evaluation_and_competency_update(self):
        """Verify assessment answers scoring and closed-loop competency update."""
        assessment = Assessment.objects.create(title="Test Assessment")
        q1 = AssessmentQuestion.objects.create(
            assessment=assessment,
            skill=self.skill_reg,
            question_text="Q1 text",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_option="A",
            explanation="Exp 1"
        )
        q2 = AssessmentQuestion.objects.create(
            assessment=assessment,
            skill=self.skill_reg,
            question_text="Q2 text",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_option="B",
            explanation="Exp 2"
        )

        # Submit answers: q1 correct ('A'), q2 wrong ('C') -> 50%
        submitted = {q1.id: 'A', q2.id: 'C'}
        attempt = CompetencyService.evaluate_assessment_submission(self.user, assessment, submitted)

        self.assertEqual(attempt.score_percentage, 50.0)
        self.assertEqual(attempt.correct_answers, 1)
        self.assertEqual(attempt.total_questions, 2)

        # Verify updated competency for Regression:
        # Prior: 35.0, New score: 50.0. Blend: 35*0.4 + 50*0.6 = 14 + 30 = 44.0%
        comp = UserCompetency.objects.get(user=self.user, skill=self.skill_reg)
        self.assertEqual(comp.current_level, 44.0)
