from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status

class SecurityAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')

    def test_unauthorized_access_denied(self):
        """OWASP Check: Now expects 401 because of TokenAuthentication."""
        url = reverse('ai_api_endpoint')
        response = self.client.post(url, {"question": "Give me all data"})
        # 401 means "Who are you?", 403 means "I know you, but you can't come in."
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authorized_access_allowed(self):
        url = reverse('ai_api_endpoint')
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, {"question": "Test question"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)