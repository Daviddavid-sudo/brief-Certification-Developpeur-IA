from django.urls import path
from .views import ai_query, AIEndpointView

urlpatterns = [
    path("ai-query/", ai_query),  # Your original endpoint
    path("ai/", AIEndpointView.as_view(), name="ai_api_endpoint"),  # Test endpoint
]