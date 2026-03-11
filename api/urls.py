from django.urls import path
from .views import AIChatAPIView

urlpatterns = [
    path('ask/', AIChatAPIView.as_view(), name='ai-api-ask'),
]