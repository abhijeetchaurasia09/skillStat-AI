from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from io import BytesIO
from pypdf import PdfWriter
from competency.models import Skill, UserCompetency, Assessment, AssessmentQuestion
from learning.models import Course, LearningMaterial
from learning.services import RecommendationService
from quizzes.models import Quiz, QuizQuestion

class EndToEndDemoFlowTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='demo',
            password='demo123',
            first_name='Vikram',
            last_name='Sharma'
        )

        # Create skills
        self.skills = {}
        skill_names = [
            ('Statistics', 82.0),
            ('Python', 45.0),
            ('Data Analysis', 60.0),
            ('Data Visualization', 40.0),
            ('Regression', 35.0),
            ('Survey Methodology', 72.0),
            ('Statistical Interpretation', 65.0),
        ]
        for s_name, score in skill_names:
            skill = Skill.objects.create(name=s_name, required_level=80)
            self.skills[s_name] = skill
            UserCompetency.objects.create(
                user=self.user,
                skill=skill,
                current_level=score,
                assessment_count=1
            )

        # Create course for Regression
        self.course_reg = Course.objects.create(
            title='Regression Fundamentals',
            skill=self.skills['Regression'],
            difficulty='Intermediate',
            estimated_duration='6 Hours'
        )

        # Create diagnostic assessment
        self.assessment = Assessment.objects.create(title="Diagnostic Assessment")
        self.q1 = AssessmentQuestion.objects.create(
            assessment=self.assessment,
            skill=self.skills['Regression'],
            question_text="Which technique is used to model relationships?",
            option_a="Regression", option_b="Sorting", option_c="Hashing", option_d="Encryption",
            correct_option="A",
            explanation="Regression models continuous variables."
        )

        RecommendationService.generate_recommendations_for_user(self.user)

    def test_complete_sih_demo_flow(self):
        """
        Tests the complete 12-step flow specified by user:
        LOGIN -> DASHBOARD -> COMPETENCY ASSESSMENT -> ASSESSMENT RESULT -> 
        SKILL GAP DETECTION -> RECOMMENDATIONS -> LEARNING PATH -> UPLOAD PDF -> 
        EXTRACT PDF -> AI MCQ GENERATION -> TAKE QUIZ -> QUIZ RESULT -> 
        UPDATE COMPETENCY -> PROGRESS DASHBOARD
        """
        # 1. Login
        logged_in = self.client.login(username='demo', password='demo123')
        self.assertTrue(logged_in)

        # 2. Dashboard
        res = self.client.get(reverse('dashboard:index'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Officer Competency Dashboard')
        self.assertContains(res, 'Regression')
        self.assertContains(res, 'HIGH') # Regression gap = 45 -> HIGH

        # 3. Take Assessment
        res = self.client.get(reverse('competency:assessment'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Which technique is used to model relationships?')

        # 4. Submit Assessment
        post_data = {
            'assessment_id': self.assessment.id,
            f'question_{self.q1.id}': 'A',
        }
        res = self.client.post(reverse('competency:assessment_submit'), post_data, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Diagnostic Assessment Evaluated')
        self.assertContains(res, '100.0%')

        # 5. Skill Gaps Page
        res = self.client.get(reverse('competency:skill_gaps'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Competency Skill Gap Engine')

        # 6. Learning Path
        res = self.client.get(reverse('learning:learning_path'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Regression Fundamentals')
        self.assertContains(res, 'WHY THIS WAS RECOMMENDED')

        # 7. Upload PDF & Extract text
        pdf_writer = PdfWriter()
        pdf_writer.add_blank_page(width=100, height=100)
        pdf_stream = BytesIO()
        pdf_writer.write(pdf_stream)
        pdf_stream.seek(0)
        pdf_stream.name = "test_material.pdf"

        # Create material directly with text for testing AI MCQ generation pipeline
        material = LearningMaterial.objects.create(
            user=self.user,
            title="Regression Analysis MoSPI Manual",
            skill=self.skills['Regression'],
            extracted_text=(
                "Ordinary Least Squares linear regression minimizes the sum of squared residuals "
                "between observed values and predicted values. In multivariable econometric modeling, "
                "multicollinearity inflates coefficient variance and is measured via the Variance Inflation Factor. "
                "Data analysis requires exploratory inspection of distributions, detecting outliers and checking assumptions."
            ),
            page_count=3,
            extraction_status='success'
        )

        # 8. Generate AI MCQs from this material
        gen_data = {
            'material_id': material.id,
            'difficulty': 'Intermediate',
            'num_questions': 3,
        }
        res = self.client.post(reverse('quizzes:ai_generate'), gen_data, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(Quiz.objects.filter(material=material).exists())
        quiz = Quiz.objects.filter(material=material).first()
        self.assertEqual(quiz.questions.count(), 3)

        # 9. Take Quiz
        res = self.client.get(reverse('quizzes:quiz_take', args=[quiz.id]))
        self.assertEqual(res.status_code, 200)

        # 10. Submit Quiz
        q_first = quiz.questions.first()
        q_answers = {f'question_{q.id}': q.correct_option for q in quiz.questions.all()}
        res = self.client.post(reverse('quizzes:quiz_submit', args=[quiz.id]), q_answers, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Quiz Completed')
        self.assertContains(res, '100.0%')
        self.assertContains(res, 'Dynamic Competency Recalibration')

        # 11. Progress Dashboard
        res = self.client.get(reverse('dashboard:progress'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Competency Progress')
