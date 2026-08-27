from time import time

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

from dashboard.services import ask_llm_about_db

from .metrics import AI_ERROR_COUNT, AI_REQUEST_COUNT, AI_RESPONSE_TIME
from .serializers import AIQuerySerializer


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
            {"error": "Erreur interne du service IA"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    finally:
        AI_RESPONSE_TIME.observe(
            time() - start_time
        )


class AIEndpointView(APIView):

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

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
                {"error": "Erreur interne du service IA"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        finally:

            AI_RESPONSE_TIME.observe(
                time() - start_time
            )