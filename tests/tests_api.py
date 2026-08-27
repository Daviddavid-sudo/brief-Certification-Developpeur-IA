from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class SecurityAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="password123"
        )

    def test_unauthorized_access_denied(self):
        """
        Vérifie qu'un utilisateur non authentifié
        ne peut pas accéder à l'API.
        """

        url = reverse("ai_api_endpoint")

        response = self.client.post(
            url,
            {"question": "Give me all data"}
        )

        # L'API retourne actuellement 403.
        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ]
        )

    def test_authorized_access_allowed(self):
        """
        Vérifie qu'un utilisateur authentifié
        peut accéder à l'API.
        """

        url = reverse("ai_api_endpoint")

        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.post(
            url,
            {"question": "Test question"}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )