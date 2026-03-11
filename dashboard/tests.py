from django.test import TestCase
from dashboard.services import ask_llm_about_db, execute_ai_sql

class AIRobustnessTests(TestCase):
    
    def test_ai_service_connection(self):
        """Verifies the AI service doesn't crash on a basic question."""
        # Note: In a real CI, you'd 'mock' the API call to avoid using credits
        response = ask_llm_about_db("Bonjour")
        self.assertIsInstance(response, str)

    def test_sql_executor_security(self):
        """OWASP Security Test: Ensure non-SELECT queries are blocked."""
        malicious_sql = "SQLQuery: DELETE FROM dashboard_population;"
        result = execute_ai_sql(malicious_sql)
        self.assertTrue("Erreur" in result or result is None)
        
    def test_accessibility_tags_present(self):
        """Basic WCAG check: Ensure labels exist."""
        response = self.client.get('/assistant/')
        self.assertContains(response, 'aria-label=') # Assumes you added this to your input