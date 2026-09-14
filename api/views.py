from time import time

from django.db.models import Sum

from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from dashboard.models import ActiviteCommerciale
from dashboard.services import ask_llm_about_db

from .metrics import AI_ERROR_COUNT, AI_REQUEST_COUNT, AI_RESPONSE_TIME
from .serializers import AIQuerySerializer


# ============================================================
# API IA
# ============================================================

@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def ai_query(request):

    AI_REQUEST_COUNT.inc()

    start_time = time()

    serializer = AIQuerySerializer(data=request.data)

    if not serializer.is_valid():

        AI_ERROR_COUNT.inc()

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    question = serializer.validated_data["question"]

    try:

        answer = ask_llm_about_db(question)

        print("===== AI REQUEST =====")
        print("User :", request.user.username)
        print("Question :", question)
        print("Answer :", answer)
        print("======================")

        return Response({
            "question": question,
            "answer": answer
        })

    except Exception as e:

        print("AI ERROR :", e)

        AI_ERROR_COUNT.inc()

        return Response(
            {
                "error": "Erreur interne du service IA"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    finally:

        AI_RESPONSE_TIME.observe(
            time() - start_time
        )


# ============================================================
# API IA - VERSION CLASS BASED
# ============================================================

class AIEndpointView(APIView):

    authentication_classes = [
        SessionAuthentication
    ]

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        AI_REQUEST_COUNT.inc()

        start_time = time()

        serializer = AIQuerySerializer(
            data=request.data
        )

        if not serializer.is_valid():

            AI_ERROR_COUNT.inc()

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        question = serializer.validated_data[
            "question"
        ]

        try:

            answer = ask_llm_about_db(
                question
            )

            print("===== AI REQUEST =====")
            print(
                "User :",
                request.user.username
            )
            print(
                "Question :",
                question
            )
            print(
                "Answer :",
                answer
            )
            print("======================")

            return Response({
                "question": question,
                "answer": answer
            })

        except Exception as e:

            print(
                "AI ERROR :",
                e
            )

            AI_ERROR_COUNT.inc()

            return Response(
                {
                    "error":
                        "Erreur interne du service IA"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        finally:

            AI_RESPONSE_TIME.observe(
                time() - start_time
            )


# ============================================================
# API PREDICTION CA 2030
# ============================================================

@api_view(["GET"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def prediction(request):

    try:

        # ----------------------------------------------------
        # Récupération du CA 2024 par département
        # ----------------------------------------------------

        ventes_2025 = (
            ActiviteCommerciale.objects
            .filter(
                annee=2024
            )
            .values(
                "code_dept"
            )
            .annotate(
                ca_2024=Sum("ca_tot")
            )
            .order_by(
                "code_dept"
            )
        )

        predictions = []

        # ----------------------------------------------------
        # Calcul de la prédiction
        # ----------------------------------------------------

        for vente in ventes_2025:

            ca_2024 = float(
                vente["ca_2024"] or 0
            )

            ca_2030 = (
                ca_2024 * 0.75
            )

            predictions.append({
                "code_dept":
                    vente["code_dept"],

                "ca_2024":
                    round(
                        ca_2024,
                        2
                    ),

                "ca_2030":
                    round(
                        ca_2030,
                        2
                    )
            })

        # ----------------------------------------------------
        # Réponse API
        # ----------------------------------------------------

        return Response({

            "success":
                True,

            "model":
                "CA 2030 = CA 2024 × 0.75",

            "year_reference":
                2024,

            "prediction_year":
                2030,

            "predictions":
                predictions

        })

    except Exception as e:

        print(
            "PREDICTION ERROR:",
            e
        )

        return Response(
            {
                "success":
                    False,

                "error":
                    "Erreur interne du service de prédiction"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )