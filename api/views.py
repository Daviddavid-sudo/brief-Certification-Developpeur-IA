from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from dashboard.services import ask_llm_about_db
# ADD THIS IMPORT:
from .serializers import AIChatSerializer

class AIChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 1. Pass the raw data to the serializer
        serializer = AIChatSerializer(data=request.data)
        
        # 2. Check if the data is valid (OWASP Security: Data Validation)
        if serializer.is_valid():
            question = serializer.validated_data['question']
            answer = ask_llm_about_db(question)
            return Response({"answer": answer}, status=status.HTTP_200_OK)
        
        # 3. Return errors if the 'question' field is missing or malformed
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)