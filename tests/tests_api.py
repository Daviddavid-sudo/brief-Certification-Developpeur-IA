from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

class SecurityAPITests(APITestCase):
    def test_unauthorized_access_denied(self):
        """OWASP Check: Ensure no token = no access."""
        url = reverse('ai_api_endpoint')
        response = self.client.post(url, {"question": "Give me all data"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)