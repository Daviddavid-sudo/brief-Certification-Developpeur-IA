from unittest.mock import MagicMock, patch

from django.test import TestCase

from dashboard.services import AI_REQUEST_COUNT, ask_llm_about_db


class MetricsMonitoringTests(TestCase):
    def test_metrics_incremented(self):
        """Verify Prometheus counters increment after AI call."""
        
        # 1. Get initial value
        # Using ._value.get() is correct for the prometheus_client library
        initial_count = AI_REQUEST_COUNT._value.get()

        # 2. Trigger the action while Mocking the external dependencies
        # This prevents the test from actually trying to call the Groq API or DB
        with patch("dashboard.services.ChatGroq"):
            with patch("dashboard.services.SQLDatabase.from_uri"):
                with patch("dashboard.services.SQLDatabaseChain.from_llm") as mocked_chain:
                    
                    # Setup the mock return value so it doesn't crash
                    mock_instance = MagicMock()
                    mock_instance.invoke.return_value = {"result": "Test Answer"}
                    mocked_chain.return_value = mock_instance

                    ask_llm_about_db("How many people live in Paris?")

        # 3. Get new value
        new_count = AI_REQUEST_COUNT._value.get()

        # 4. Assert
        self.assertGreater(
            new_count, 
            initial_count, 
            "The counter AI_REQUEST_COUNT should increment even if the API call is mocked."
        )