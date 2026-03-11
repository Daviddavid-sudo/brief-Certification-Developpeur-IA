from django.urls import path
from .views import AIEndpointView, ai_query

urlpatterns = [
    # This 'name' must match the reverse() in your tests
    path('api/ai-endpoint/', AIEndpointView.as_view(), name='ai_api_endpoint'),
    path('api/ai-query/', ai_query, name='ai_query'),
]