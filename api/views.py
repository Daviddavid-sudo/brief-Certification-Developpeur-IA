from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import AIQuerySerializer
from dashboard.services import ask_llm_about_db


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