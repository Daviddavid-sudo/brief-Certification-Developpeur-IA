from django.test import TestCase
from django.urls import reverse

class BasicTests(TestCase):
    def test_home_page_status_code(self):
        # Checks if the URL named 'population_view' (or whatever your home is) works
        # If this returns a 500 error because of a typo, the CI will FAIL.
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_db_is_accessible(self):
        # Verifies the CI can actually talk to your SQLite DB
        from dashboard.models import Population  # Replace with one of your actual models
        count = Population.objects.count()
        self.assertGreaterEqual(count, 0)