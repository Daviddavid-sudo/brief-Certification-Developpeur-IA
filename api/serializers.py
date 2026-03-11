from rest_framework import serializers

class AIQuerySerializer(serializers.Serializer):
    question = serializers.CharField(max_length=500)