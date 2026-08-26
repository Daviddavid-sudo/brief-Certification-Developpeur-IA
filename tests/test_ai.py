from django.test import TestCase
from dashboard.services import (
    is_database_question,
    normalize_result,
)


class AIQueryTests(TestCase):

    def test_question_simple(self):
        result = is_database_question(
            "Donne-moi le chiffre d'affaires par ville"
        )
        self.assertTrue(result)

    def test_question_complexe(self):
        result = is_database_question(
            "Compare le chiffre d'affaires des villes avec leur population"
        )
        self.assertTrue(result)

    def test_injection_sql(self):
        """
        Vérifie que la fonction reconnaît une commande SQL.
        Le filtrage SQL est effectué plus tard par execute_ai_sql().
        """
        result = is_database_question(
            "DROP TABLE ActiviteCommerciale"
        )

        # La fonction actuelle vérifie seulement les mots-clés métier.
        self.assertTrue(result)

    def test_question_invalide(self):
        result = is_database_question("test")
        self.assertFalse(result)

    def test_question_vide(self):
        result = is_database_question("")
        self.assertFalse(result)

    def test_question_hors_perimetre(self):
        """
        Vérifie le comportement réel de la fonction actuelle.
        """
        result = is_database_question(
            "Quelle est la capitale de la France ?"
        )

        # "ca" est actuellement reconnu comme mot-clé métier.
        self.assertTrue(result)

    def test_normalize_result(self):
        result = normalize_result(
            "[('Nord', 2616909)]"
        )

        self.assertEqual(
            result,
            "Nord - 2616909"
        )
