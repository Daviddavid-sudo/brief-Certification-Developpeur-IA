from django.test import TestCase
from unittest.mock import patch, MagicMock

from dashboard.services import (
    ask_llm_about_db,
    is_database_question,
    normalize_result,
)


class AIQueryTests(TestCase):

    def test_question_simple(self):
        """
        Vérifie qu'une question concernant
        le chiffre d'affaires est reconnue.
        """
        result = is_database_question(
            "Donne-moi le chiffre d'affaires par ville"
        )

        self.assertTrue(result)

    def test_question_complexe(self):
        """
        Vérifie qu'une question complexe concernant
        plusieurs données métier est reconnue.
        """
        result = is_database_question(
            "Compare le chiffre d'affaires des villes avec leur population"
        )

        self.assertTrue(result)

    def test_injection_sql(self):
        """
        Vérifie qu'une commande SQL dangereuse
        n'est pas considérée comme une question métier.
        """
        result = is_database_question(
            "DROP TABLE ActiviteCommerciale"
        )

        self.assertFalse(result)

    def test_question_invalide(self):
        """
        Vérifie qu'une question invalide est refusée.
        """
        result = is_database_question(
            "test"
        )

        self.assertFalse(result)

    def test_question_vide(self):
        """
        Vérifie qu'une question vide est refusée.
        """
        result = is_database_question("")

        self.assertFalse(result)

    def test_question_hors_perimetre(self):
        """
        Vérifie qu'une question qui ne concerne pas
        les données métier est refusée.
        """
        result = is_database_question(
            "Quelle est la capitale de la France ?"
        )

        self.assertFalse(result)

    def test_normalize_result(self):
        """
        Vérifie que les résultats SQL sont correctement
        transformés en texte.
        """
        result = normalize_result(
            "[('Nord', 2616909)]"
        )

        self.assertEqual(
            result,
            "Nord - 2616909"
        )

    @patch("dashboard.services.ChatGroq")
    def test_question_population_avec_llm(self, mock_chatgroq):
        """
        Vérifie le traitement d'une question de population
        sans appeler réellement l'API Groq.
        """

        mock_llm = MagicMock()

        mock_chatgroq.return_value = mock_llm

        result = ask_llm_about_db(
            "Quel est le département avec la plus grande population ?"
        )

        self.assertIsNotNone(result)

    @patch("dashboard.services.ChatGroq")
    def test_question_hors_perimetre_sans_llm(self, mock_chatgroq):
        """
        Vérifie qu'une question hors périmètre
        ne déclenche pas d'appel au LLM.
        """

        result = ask_llm_about_db(
            "Quel temps fait-il aujourd'hui ?"
        )

        self.assertIn(
            "questions liées",
            result
        )

        mock_chatgroq.assert_not_called()