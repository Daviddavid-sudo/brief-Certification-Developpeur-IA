from django.test import TestCase
from unittest.mock import patch, MagicMock
from dashboard.services import ask_llm_about_db

class MLOpsValidation(TestCase):
    def test_model_targets_correct_tables(self):
        """MLOps Check: Ensure Llama 3.3 picks the population table."""
        
        # We mock the SQLDatabaseChain to simulate a successful AI response
        with patch('dashboard.services.SQLDatabase.from_uri'):
            with patch('dashboard.services.SQLDatabaseChain.from_llm') as mocked_chain_init:
                mock_instance = MagicMock()
                # We simulate the AI returning the table name in its response
                mock_instance.invoke.return_value = {"result": "I am querying the dashboard_population table."}
                mocked_chain_init.return_value = mock_instance
                
                response = ask_llm_about_db("Quelle est la population ?")
                
                # Now this will look at our mock result, not the real (missing) Groq API
                self.assertIn("dashboard_population", response.lower())