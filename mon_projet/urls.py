from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path

from dashboard.views import (
    CustomLoginView,
    activite_create,
    activite_delete,
    activite_list,
    activite_update,
    ai_assistant_view,
    approve_user,
    carte_population_view,
    carte_ventes_view,
    consultation_meteo,
    health_check,
    landing_page,
    product_list_view,
    register,
    reject_user,
    users_view,
)

urlpatterns = [

    # ============================================================
    # LANDING PAGE
    # ============================================================

    path(
        "",
        landing_page,
        name="landing"
    ),


    # ============================================================
    # AUTHENTIFICATION
    # ============================================================

    path(
        "login/",
        CustomLoginView.as_view(),
        name="login"
    ),


    path(
        "logout/",
        LogoutView.as_view(
            next_page="landing"
        ),
        name="logout"
    ),


    path(
        "register/",
        register,
        name="register"
    ),


    # ============================================================
    # ADMINISTRATION DJANGO
    #
    # Elle existe toujours techniquement,
    # mais elle n'est PLUS accessible depuis ton interface.
    # ============================================================

    path(
        "admin/",
        admin.site.urls
    ),


    # ============================================================
    # PROMETHEUS
    # ============================================================

    path(
        "",
        include(
            "django_prometheus.urls"
        )
    ),


    # ============================================================
    # DASHBOARD COMMERCIAL
    # ============================================================

    path(
        "carte/",
        carte_ventes_view,
        name="carte_ventes"
    ),


    # ============================================================
    # METEO
    # Accessible à tous les utilisateurs connectés
    # ============================================================

    path(
        "meteo_calendrier/",
        consultation_meteo,
        name="meteo_calendrier"
    ),


    # ============================================================
    # POPULATION
    # ============================================================

    path(
        "population/",
        carte_population_view,
        name="population"
    ),


    # ============================================================
    # ASSISTANT IA
    # ============================================================

    path(
        "assistant/",
        ai_assistant_view,
        name="ai_assistant"
    ),


    # ============================================================
    # ARTICLES
    # ============================================================

    path(
        "articles/",
        product_list_view,
        name="articles_list"
    ),


    # ============================================================
    # GESTION ACTIVITE COMMERCIALE
    # ============================================================

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


    # ============================================================
    # ADMINISTRATION INTERNE DU SITE
    # ============================================================

    path(
        "users/",
        users_view,
        name="users"
    ),


    path(
        "users/<int:user_id>/approve/",
        approve_user,
        name="approve_user"
    ),


    path(
        "users/<int:user_id>/reject/",
        reject_user,
        name="reject_user"
    ),


    # ============================================================
    # API
    # ============================================================

    path(
        "api/v1/",
        include("api.urls")
    ),


    # ============================================================
    # HEALTH CHECK
    # ============================================================

    path(
        "health/",
        health_check,
        name="health_check"
    ),

]