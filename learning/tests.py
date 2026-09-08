from django.test import TestCase
from django.contrib.auth.models import User
from competency.models import Skill, UserCompetency
from learning.models import Course, Recommendation
from learning.services import RecommendationService, IGOTIntegrationService

class LearningTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='learner1', password='password123')

        self.skill = Skill.objects.create(name='Regression', required_level=80)
        self.course = Course.objects.create(
            title='Regression Fundamentals',
            skill=self.skill,
            difficulty='Intermediate',
            estimated_duration='6 Hours',
            igot_course_id='IGOT-STAT-301'
        )

        UserCompetency.objects.create(user=self.user, skill=self.skill, current_level=35.0)

    def test_explainable_recommendation_generation(self):
        """Verify recommendations depend on user gap and produce transparent explanations."""
        recs = RecommendationService.generate_recommendations_for_user(self.user)
        self.assertEqual(len(recs), 1)

        rec = recs[0]
        self.assertEqual(rec.course, self.course)
        self.assertEqual(rec.priority, 'HIGH')
        self.assertEqual(rec.gap_points, 45.0)

        # Check explainable explanation string
        self.assertIn("You scored 35.0% in Regression", rec.reason)
        self.assertIn("resulting in a 45.0-point gap", rec.reason)
        self.assertIn("HIGH PRIORITY", rec.reason)

    def test_igot_integration_prototype(self):
        """Verify iGOT integration data contract mapping."""
        status = IGOTIntegrationService.get_connection_status()
        self.assertEqual(status['integration_mode'], 'PROTOTYPE')
        self.assertIn('iGOT Karmayogi', status['ecosystem'])

        mapped = IGOTIntegrationService.map_to_igot_competency('Regression', 35.0)
        self.assertEqual(mapped['igot_code'], 'COMP-STAT-009')
        self.assertTrue(mapped['sync_eligible'])
