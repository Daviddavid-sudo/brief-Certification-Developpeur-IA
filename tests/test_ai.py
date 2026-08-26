from django.test import TestCase
from dashboard.services import (
    is_database_question,
    normalize_result,
)


class AIQueryTests(TestCase):

    def test_question_simple(self):
        """Une question métier est acceptée."""
        result = is_database_question(
            "Donne-moi le chiffre d'affaires par ville"
        )

        self.assertTrue(result)

    def test_question_complexe(self):
        """Une question métier complexe est acceptée."""
        result = is_database_question(
            "Compare le chiffre d'affaires des villes avec leur population"
        )

        self.assertTrue(result)

    def test_injection_sql(self):
        """Une commande SQL dangereuse est refusée."""
        result = is_database_question(
            "DROP TABLE ActiviteCommerciale"
        )

        self.assertFalse(result)

    def test_question_invalide(self):
        """Une entrée invalide est refusée."""
        result = is_database_question("test")

        self.assertFalse(result)

    def test_question_vide(self):
        """Une question vide est refusée."""
        result = is_database_question("")

        self.assertFalse(result)

    def test_question_hors_perimetre(self):
        """Une question hors périmètre est refusée."""
        result = is_database_question(
            "Quelle est la capitale de la France ?"
        )

        self.assertFalse(result)

    def test_normalize_result(self):
        """Le résultat SQL est correctement transformé."""
        result = normalize_result(
            "[('Nord', 2616909)]"
        )

        self.assertEqual(
            result,
            "Nord - 2616909"
        )
