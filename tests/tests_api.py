from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status

class SecurityAPITests(APITestCase):
    def setUp(self):
        # Create a test user for the "Authorized" test
        self.user = User.objects.create_user(username='testuser', password='password123')

    def test_unauthorized_access_denied(self):
        """OWASP Check: Ensure no token = no access (Status 401)."""
        url = reverse('ai_api_endpoint')
        # No authentication provided
        response = self.client.post(url, {"question": "Give me all data"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authorized_access_allowed(self):
        """Ensure a logged-in user can actually use the AI (Status 200)."""
        url = reverse('ai_api_endpoint')
        # Force authenticate the client
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(url, {"question": "What is the weather?"})
        # This will return 200 now because the user is authenticated
        self.assertEqual(response.status_code, status.HTTP_200_OK)