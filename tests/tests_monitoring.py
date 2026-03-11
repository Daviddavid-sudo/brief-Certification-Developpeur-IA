import os
from django.test import TestCase
from dashboard.services import ask_llm_about_db

class MetricsMonitoringTests(TestCase):
    def test_latency_is_logged(self):
        """Monitoring Check: Verify that performance metrics are written to logs."""
        log_file = "logs/ai_metrics.log"
        ask_llm_about_db("Test monitoring query")
        
        self.assertTrue(os.path.exists(log_file))
        with open(log_file, 'r') as f:
            content = f.read()
            self.assertIn("latency", content.lower())