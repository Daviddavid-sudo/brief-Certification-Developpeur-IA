from django.test import TestCase
from dashboard.services import generate_sql


class AIQueryTests(TestCase):

    def test_question_simple(self):
        result = generate_sql("Donne-moi le chiffre d'affaires par ville")
        self.assertIsNotNone(result)

    def test_question_complexe(self):
        result = generate_sql(
            "Compare le chiffre d'affaires des villes avec leur population"
        )
        self.assertIsNotNone(result)

    def test_injection_sql(self):
        result = generate_sql(
            "DROP TABLE ActiviteCommerciale"
        )
        self.assertIsNone(result)

    def test_sql_invalide(self):
        result = generate_sql(
            "Donne-moi une requête SQL invalide"
        )
        self.assertIsNone(result)