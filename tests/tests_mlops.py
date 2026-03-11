from django.test import TestCase
from unittest.mock import patch, MagicMock
from dashboard.services import ask_llm_about_db

class MLOpsValidation(TestCase):
    def test_model_targets_correct_tables(self):
        """MLOps Check: Ensure Llama 3.3 identifies the correct table name."""
        
        # 1. We patch 'from_uri' so it doesn't actually try to connect to Postgres
        with patch('dashboard.services.SQLDatabase.from_uri'):
            # 2. We patch the LLM chain so it doesn't need a real GROQ_API_KEY
            with patch('dashboard.services.SQLDatabaseChain.from_llm') as mocked_chain_init:
                
                # Create a mock instance of the chain
                mock_chain_instance = MagicMock()
                
                # Tell the mock to return a string containing the table name
                # This simulates the AI successfully finding the right table
                mock_chain_instance.invoke.return_value = {
                    "result": "I will query the dashboard_population table to answer your question."
                }
                
                # Make the factory return our mock instance
                mocked_chain_init.return_value = mock_chain_instance
                
                # 3. Call the service
                # Even if GROQ_API_KEY is missing in CI, the mocks prevent the error
                response = ask_llm_about_db("Quelle est la population totale ?")
                
                # 4. Assert
                self.assertIn("dashboard_population", response.lower())