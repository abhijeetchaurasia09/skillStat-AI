from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

class AccountsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testofficer',
            email='testofficer@gov.in',
            password='testpassword123',
            first_name='Aditi',
            last_name='Rao'
        )

    def test_user_profile_creation(self):
        """Verify UserProfile is automatically created via post_save signal."""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIn('MoSPI', self.user.profile.department)

    def test_login_and_logout(self):
        """Test authentication flow."""
        # Valid login
        login_res = self.client.login(username='testofficer', password='testpassword123')
        self.assertTrue(login_res)

        # Profile page requires login
        res = self.client.get(reverse('accounts:profile'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Aditi')

        # Logout
        logout_res = self.client.post(reverse('accounts:logout'))
        self.assertEqual(logout_res.status_code, 302)

    def test_registration_flow(self):
        """Test user registration endpoint."""
        res = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'first_name': 'Rahul',
            'last_name': 'Mehta',
            'email': 'rahul@gov.in',
            'department': 'MoSPI',
            'job_role': 'Statistical Investigator',
            'password': 'password123',
            'confirm_password': 'password123',
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
