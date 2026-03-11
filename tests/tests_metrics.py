from django.test import TestCase
from dashboard.services import ask_llm_about_db
from prometheus_client import REGISTRY

class MetricsMonitoringTests(TestCase):
    def test_metrics_incremented(self):
        """Verify Prometheus counters increment after AI call."""
        # Initial metric value
        initial_count = next(
            (m.samples[0].value for m in REGISTRY.collect() if m.name == "ai_request_total"),
            0
        )

        ask_llm_about_db("Test metrics query")

        # New metric value
        new_count = next(
            (m.samples[0].value for m in REGISTRY.collect() if m.name == "ai_request_total"),
            0
        )

        self.assertGreater(new_count, initial_count)