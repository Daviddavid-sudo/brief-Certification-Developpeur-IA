from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from dashboard.services import ask_llm_about_db

class AIChatAPIView(APIView):
    # SECURITY: Only users with a token can access this (OWASP requirement)
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AIChatSerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.validated_data['question']
            answer = ask_llm_about_db(question) # Calls your service
            return Response({"answer": answer}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)