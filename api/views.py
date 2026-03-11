from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import AIQuerySerializer
from dashboard.services import ask_llm_about_db

# 1. Protected Function-based view
@api_view(["POST"])
@permission_classes([IsAuthenticated])
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


# 2. Protected Class-based view (matches your test reverse look-up)
class AIEndpointView(APIView):
    """
    API endpoint for asking questions to the AI.
    Requires authentication to pass OWASP security tests.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AIQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        question = serializer.validated_data["question"]
        
        # This service call should trigger your Prometheus increment
        answer = ask_llm_about_db(question)

        return Response({
            "question": question,
            "answer": answer
        })