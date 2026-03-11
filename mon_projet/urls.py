"""
URL configuration for mon_projet project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# On importe directement les fonctions depuis l'application dashboard
from dashboard.views import carte_ventes_view, consultation_meteo, carte_population_view, ai_assistant_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', carte_ventes_view, name='home'), 
    path('carte/', carte_ventes_view, name='carte_ventes'),
    path('meteo_calendrier/', consultation_meteo, name='meteo_calendrier'),
    path('population/', carte_population_view, name='population'),
    path('assistant/', ai_assistant_view, name='ai_assistant'),
    path('api/v1/', include('api.urls')),
]
