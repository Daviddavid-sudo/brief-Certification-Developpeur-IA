from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from .serializers import AIQuerySerializer
from dashboard.services import ask_llm_about_db

# 1. Protected Function-based view
# This is likely your main API endpoint used by the frontend
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def ai_query(request):
    serializer = AIQuerySerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    question = serializer.validated_data["question"]
    answer = ask_llm_about_db(question)

    return Response({
        "question": question,
        "answer": answer
    })


# 2. Protected Class-based view
# This matches the 'ai_api_endpoint' used in your unit tests
class AIEndpointView(APIView):
    """
    API endpoint for asking questions to the AI.
    Requires TokenAuthentication to pass OWASP security tests (Status 401).
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AIQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question = serializer.validated_data["question"]
        
        # This service call triggers the Prometheus increment (AI_REQUEST_COUNT)
        answer = ask_llm_about_db(question)

        return Response({
            "question": question,
            "answer": answer
        })