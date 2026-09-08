from django.test import TestCase
from django.contrib.auth.models import User
from competency.models import Skill, UserCompetency
from quizzes.models import Quiz, QuizQuestion, QuizAttempt
from quizzes.services import QuizService

class QuizzesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='quiztaker', password='password123')
        self.skill = Skill.objects.create(name='Regression', required_level=80)
        self.comp = UserCompetency.objects.create(user=self.user, skill=self.skill, current_level=35.0)

        self.sample_questions = [
            {
                'question': 'What is OLS?',
                'option_a': 'Ordinary Least Squares',
                'option_b': 'Online Linear System',
                'option_c': 'Option C',
                'option_d': 'Option D',
                'correct_option': 'A',
                'explanation': 'OLS minimizes squared residuals.',
                'skill': 'Regression'
            },
            {
                'question': 'What does R-squared measure?',
                'option_a': 'Explained Variance',
                'option_b': 'Sample Size',
                'option_c': 'Option C',
                'option_d': 'Option D',
                'correct_option': 'A',
                'explanation': 'R-squared measures goodness of fit.',
                'skill': 'Regression'
            }
        ]

    def test_quiz_creation_and_scoring(self):
        """Test creating a quiz and calculating score and competency update."""
        quiz = QuizService.create_quiz_from_mcqs(
            user=self.user,
            title='Regression Practice Quiz',
            questions_data=self.sample_questions,
            skill=self.skill,
            ai_mode='mock'
        )

        self.assertEqual(quiz.questions.count(), 2)
        q1 = quiz.questions.first()
        q2 = quiz.questions.last()

        # Both correct -> 100%
        attempt = QuizService.evaluate_quiz_submission(
            user=self.user,
            quiz=quiz,
            user_answers_dict={q1.id: 'A', q2.id: 'A'}
        )

        self.assertEqual(attempt.score_percentage, 100.0)
        self.assertEqual(attempt.before_competency, 35.0)
        # Gain = (100 - 35) * 0.35 = 65 * 0.35 = 22.75 -> 22.8
        self.assertGreater(attempt.competency_gain, 0)
        self.assertGreater(attempt.after_competency, 35.0)

        # Confirm user competency updated in database
        self.comp.refresh_from_db()
        self.assertEqual(self.comp.current_level, attempt.after_competency)
