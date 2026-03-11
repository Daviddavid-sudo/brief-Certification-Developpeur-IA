from rest_framework import serializers

class AIChatSerializer(serializers.Serializer):
    question = serializers.CharField(required=True, help_text="La question à poser à l'IA")