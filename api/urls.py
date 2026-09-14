from django.urls import path

from .views import (
    AIEndpointView,
    ai_query,
    prediction,
)


urlpatterns = [

    # API IA
    path(
        'ai-endpoint/',
        AIEndpointView.as_view(),
        name='ai_api_endpoint'
    ),

    path(
        'ai-query/',
        ai_query,
        name='ai_query'
    ),

    # API prédiction CA 2030
    path(
        'prediction/',
        prediction,
        name='prediction'
    ),

]