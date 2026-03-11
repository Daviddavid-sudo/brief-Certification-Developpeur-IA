from django.test import TestCase
from dashboard.services import ask_llm_about_db

class MLOpsValidation(TestCase):
    def test_model_targets_correct_tables(self):
        """MLOps Check: Ensure Llama 3.3 picks the population table for population questions."""
        response = ask_llm_about_db("Quelle est la population de Paris ?")
        # We check the 'thought process' of the AI to ensure it's not hallucinating tables
        self.assertIn("dashboard_population", response.lower())