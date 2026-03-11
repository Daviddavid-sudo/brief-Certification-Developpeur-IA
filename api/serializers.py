from rest_framework import serializers

class AIChatSerializer(serializers.Serializer):
    # This validates that 'question' is a string and is required
    question = serializers.CharField(
        required=True, 
        min_length=3,
        error_messages={
            "required": "Le champ 'question' est obligatoire.",
            "blank": "La question ne peut pas être vide."
        }
    )