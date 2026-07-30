from django.contrib import admin
from django.urls import path, include

from dashboard.views import (
    carte_ventes_view,
    consultation_meteo,
    carte_population_view,
    ai_assistant_view,
    health_check,
    product_list_view,
    CustomLoginView,
    activite_list,
    activite_create,
    activite_update,
    activite_delete,
)

from django.contrib.auth.views import LogoutView


urlpatterns = [

    # Monitoring Prometheus
    path('', include('django_prometheus.urls')),

    # Administration Django
    path('admin/', admin.site.urls),


    # Dashboard principal
    path(
        '',
        carte_ventes_view,
        name='home'
    ),

    path(
        'carte/',
        carte_ventes_view,
        name='carte_ventes'
    ),

    path(
        'meteo_calendrier/',
        consultation_meteo,
        name='meteo_calendrier'
    ),

    path(
        'population/',
        carte_population_view,
        name='population'
    ),


    # Assistant IA
    path(
        'assistant/',
        ai_assistant_view,
        name='ai_assistant'
    ),


    # API
    path(
        'api/v1/',
        include('api.urls')
    ),


    # Health Check
    path(
        'health/',
        health_check,
        name='health_check'
    ),


    # Articles
    path(
        'articles/',
        product_list_view,
        name='articles_list'
    ),


    # Authentification
    path(
        "login/",
        CustomLoginView.as_view(),
        name="login"
    ),

    path(
        "logout/",
        LogoutView.as_view(next_page="login"),
        name="logout"
    ),


    # CRUD Activité commerciale
    path(
        "activites/",
        activite_list,
        name="activite_list"
    ),

    path(
        "activite/create/",
        activite_create,
        name="activite_create"
    ),

    path(
        "activite/update/<int:id>/",
        activite_update,
        name="activite_update"
    ),

    path(
        "activite/delete/<int:id>/",
        activite_delete,
        name="activite_delete"
    ),

]