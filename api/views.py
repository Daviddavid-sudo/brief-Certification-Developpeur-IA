from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import AIQuerySerializer
from dashboard.services import ask_llm_about_db


# Your original function-based view
@api_view(["POST"])
def ai_query(request):
    serializer = AIQuerySerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    question = serializer.validated_data["question"]
    answer = ask_llm_about_db(question)

    return Response({
        "question": question,
        "answer": answer
    })


# Class-based view for the test
class AIEndpointView(APIView):
    """
    API endpoint for asking questions to the AI (needed for tests).
    """
    def post(self, request):
        serializer = AIQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        question = serializer.validated_data["question"]
        answer = ask_llm_about_db(question)

        return Response({
            "question": question,
            "answer": answer
        })