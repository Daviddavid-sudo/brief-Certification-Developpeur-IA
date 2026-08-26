from django.test import TestCase
from unittest.mock import patch, MagicMock

from dashboard.services import (
    ask_llm_about_db,
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
        result = is_database_question(
            "DROP TABLE ActiviteCommerciale"
        )
        self.assertFalse(result)

    def test_question_invalide(self):
        result = is_database_question("test")
        self.assertFalse(result)

    def test_question_vide(self):
        result = is_database_question("")
        self.assertFalse(result)

    def test_question_hors_perimetre(self):
        result = is_database_question(
            "Quelle est la capitale de la France ?"
        )
        self.assertFalse(result)

    def test_normalize_result(self):
        result = normalize_result(
            "[('Nord', 2616909)]"
        )
        self.assertEqual(
            result,
            "Nord - 2616909"
        )

    @patch("dashboard.services.ChatGroq")
    def test_question_population_avec_llm(self, mock_chatgroq):
        mock_llm = MagicMock()
        mock_chatgroq.return_value = mock_llm

        result = ask_llm_about_db(
            "Quel est le département avec la plus grande population ?"
        )

        self.assertIsNotNone(result)

    @patch("dashboard.services.ChatGroq")
    def test_question_hors_perimetre_sans_llm(self, mock_chatgroq):
        result = ask_llm_about_db(
            "Quel temps fait-il aujourd'hui ?"
        )

        self.assertIn("questions liées", result)
        mock_chatgroq.assert_not_called()
