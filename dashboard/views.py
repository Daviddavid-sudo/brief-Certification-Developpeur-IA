import os
import io
import urllib
import base64
import json
import logging

import pandas as pd
import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import (
    ActiviteCommerciale,
    MeteoArchive,
    Population,
    UserProfile,
)

from dashboard.services import ask_llm_about_db, execute_ai_sql


# ============================================================
# AUTHENTIFICATION
# ============================================================

class CustomLoginView(LoginView):
    template_name = "dashboard/login.html"
    redirect_authenticated_user = True


def is_admin(user):
    return user.is_authenticated and user.is_staff


def approved_required(view_func):
    """
    Autorise :
    - les administrateurs ;
    - les utilisateurs dont le compte est approuvé.

    Les utilisateurs non approuvés sont redirigés vers Météo.
    """

    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("/login/")

        # Administrateur = accès complet
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)

        # Vérification du profil
        if not hasattr(request.user, "profile"):
            messages.warning(
                request,
                "Votre compte est en attente d'approbation par un administrateur."
            )
            return redirect("meteo_calendrier")

        # Compte non approuvé
        if not request.user.profile.is_approved:
            messages.warning(
                request,
                "Votre compte est en attente d'approbation par un administrateur."
            )
            return redirect("meteo_calendrier")

        return view_func(request, *args, **kwargs)

    return wrapper


def register(request):

    if request.method == "POST":

        form = UserCreationForm(request.POST)

        if form.is_valid():

            user = form.save()

            UserProfile.objects.create(
                user=user,
                is_approved=False
            )

            login(request, user)

            return redirect("meteo_calendrier")

    else:
        form = UserCreationForm()

    return render(
        request,
        "dashboard/register/register.html",
        {"form": form}
    )


# ============================================================
# MONITORING
# ============================================================

logger = logging.getLogger("ai_monitoring")


def health_check(request):

    checks = {}
    is_healthy = True

    try:

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        checks["database"] = "UP"

    except Exception as e:

        checks["database"] = f"DOWN: {str(e)}"
        is_healthy = False

    api_key = os.getenv("GROQ_API_KEY")

    checks["ai_service"] = (
        "READY"
        if api_key
        else "MISSING_KEY"
    )

    if not api_key:
        is_healthy = False

    status_code = 200 if is_healthy else 503

    return JsonResponse(
        {
            "status": (
                "healthy"
                if is_healthy
                else "unhealthy"
            ),
            "timestamp": datetime.now().isoformat(),
            "components": checks
        },
        status=status_code
    )


# ============================================================
# UTILITAIRE GRAPHIQUES
# ============================================================

def get_plot_uri():

    buf = io.BytesIO()

    plt.savefig(
        buf,
        format="png",
        bbox_inches="tight"
    )

    buf.seek(0)

    uri = urllib.parse.quote(
        base64.b64encode(
            buf.read()
        )
    )

    plt.close()

    return uri


# ============================================================
# PRODUITS
# ============================================================

@approved_required
def product_list_view(request):

    file_path = os.path.join(
        settings.BASE_DIR,
        "data",
        "scraped_products.json"
    )

    data = []

    if os.path.exists(file_path):

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

        except Exception as e:

            logger.error(
                f"Erreur lecture produits : {e}"
            )

    return render(
        request,
        "dashboard/articles.html",
        {
            "products": data
        }
    )


# ============================================================
# CARTE DES VENTES
# ============================================================

@approved_required
def carte_ventes_view(request):

    selected_year = 2024

    selected_month = request.GET.get(
        "month",
        timezone.now().month
    )

    path_geojson = os.path.join(
        settings.BASE_DIR,
        "data",
        "departements.geojson"
    )

    france = gpd.read_file(path_geojson)

    ventes_qs = (
        ActiviteCommerciale.objects
        .filter(
            mois=selected_month,
            annee=selected_year
        )
        .values(
            "code_dept",
            "ca_tot"
        )
    )

    df_ventes = pd.DataFrame(
        list(ventes_qs)
    )

    max_pop_obj = (
        Population.objects
        .order_by("-pop")
        .first()
    )

    vmax_fixed = (
        max_pop_obj.pop * 6
        if max_pop_obj
        else 1000000
    )

    fig, ax = plt.subplots(
        1,
        1,
        figsize=(10, 10)
    )

    if not df_ventes.empty:

        df_regroupe = (
            df_ventes
            .groupby("code_dept")["ca_tot"]
            .sum()
            .reset_index()
        )

        france = france.merge(
            df_regroupe,
            left_on="code",
            right_on="code_dept",
            how="left"
        )

        france.plot(
            column="ca_tot",
            ax=ax,
            legend=True,
            cmap="OrRd",
            vmin=0,
            vmax=vmax_fixed,
            missing_kwds={
                "color": "lightgrey"
            },
            legend_kwds={
                "label": "Chiffre d'Affaires (€)"
            }
        )

    else:

        france.plot(
            ax=ax,
            color="lightgrey"
        )

    ax.set_axis_off()

    ax.set_title(
        f"Ventes par Département - Mois {selected_month}"
    )

    return render(
        request,
        "dashboard/carte.html",
        {
            "data_map": get_plot_uri(),
            "selected_month": int(selected_month),
            "months_range": range(1, 13)
        }
    )


# ============================================================
# METEO
# ACCESSIBLE AUX UTILISATEURS CONNECTÉS
# ============================================================

@login_required
def consultation_meteo(request):

    resultats = None
    data_map = None

    date_selectionnee = request.GET.get(
        "date_choisie"
    )

    if date_selectionnee:

        try:

            dt_obj = datetime.strptime(
                date_selectionnee,
                "%Y-%m-%d"
            )

            resultats = MeteoArchive.objects.filter(
                annee=dt_obj.year,
                mois=dt_obj.month,
                jour=dt_obj.day
            )

            path_geojson = os.path.join(
                settings.BASE_DIR,
                "data",
                "departements.geojson"
            )

            france = gpd.read_file(
                path_geojson
            )

            fig, ax = plt.subplots(
                1,
                1,
                figsize=(10, 10)
            )

            if resultats.exists():

                df_meteo = pd.DataFrame(
                    list(
                        resultats.values(
                            "dep",
                            "temp_min",
                            "temp_max"
                        )
                    )
                )

                df_meteo["dep"] = (
                    df_meteo["dep"]
                    .apply(
                        lambda x:
                        x.zfill(2)
                        if (
                            len(x) == 1
                            and x.isdigit()
                        )
                        else x
                    )
                )

                france = france.merge(
                    df_meteo,
                    left_on="code",
                    right_on="dep",
                    how="left"
                )

                france.plot(
                    column="temp_min",
                    ax=ax,
                    legend=True,
                    cmap="coolwarm",
                    missing_kwds={
                        "color": "#f0f0f0"
                    },
                    legend_kwds={
                        "label": "Température Minimale (°C)",
                        "orientation": "horizontal",
                        "pad": 0.05
                    }
                )

            else:

                france.plot(
                    ax=ax,
                    color="#f0f0f0",
                    edgecolor="white"
                )

            ax.set_axis_off()

            ax.set_title(
                f"Météo France - "
                f"{dt_obj.strftime('%d/%m/%Y')}"
            )

            data_map = get_plot_uri()

        except Exception as e:

            logger.error(
                f"Erreur Carte Météo : {e}"
            )

    return render(
        request,
        "dashboard/meteo_calendrier.html",
        {
            "resultats": resultats,
            "date_selectionnee": date_selectionnee,
            "data_map": data_map
        }
    )


# ============================================================
# POPULATION
# ============================================================

@approved_required
def carte_population_view(request):

    path_geojson = os.path.join(
        settings.BASE_DIR,
        "data",
        "departements.geojson"
    )

    france = gpd.read_file(
        path_geojson
    )

    pop_qs = (
        Population.objects
        .all()
        .values("dep", "pop")
    )

    df_pop = pd.DataFrame(
        list(pop_qs)
    )

    fig, ax = plt.subplots(
        1,
        1,
        figsize=(10, 10)
    )

    if not df_pop.empty:

        france = france.merge(
            df_pop,
            left_on="code",
            right_on="dep",
            how="left"
        )

        france.plot(
            column="pop",
            ax=ax,
            legend=True,
            cmap="YlGnBu",
            missing_kwds={
                "color": "#f5f5f5"
            },
            legend_kwds={
                "label": "Nombre d'habitants (Source INSEE)"
            }
        )

    else:

        france.plot(
            ax=ax,
            color="lightgrey"
        )

    ax.set_axis_off()

    ax.set_title(
        "Population réelle par Département"
    )

    return render(
        request,
        "dashboard/population.html",
        {
            "data_map": get_plot_uri()
        }
    )


# ============================================================
# ASSISTANT IA
# ============================================================

@approved_required
def ai_assistant_view(request):

    if request.method == "POST":

        user_query = (
            request.POST
            .get("message", "")
            .strip()
        )

        logger.info(
            f"Requête utilisateur reçue : {user_query}"
        )

        try:

            ai_raw_output = ask_llm_about_db(
                user_query
            )

            db_data = execute_ai_sql(
                ai_raw_output
            )

            if (
                isinstance(db_data, dict)
                and db_data.get("rows")
            ):

                cols = ", ".join(
                    db_data["columns"]
                )

                formatted_rows = [
                    str(
                        dict(
                            zip(
                                db_data["columns"],
                                row
                            )
                        )
                    )
                    for row in db_data["rows"][:3]
                ]

                data_str = " | ".join(
                    formatted_rows
                )

                final_response = (
                    "J'ai analysé les données. "
                    f"Voici les résultats "
                    f"({cols}) : {data_str}"
                )

            else:

                final_response = ai_raw_output

            return JsonResponse(
                {
                    "response": final_response
                }
            )

        except Exception as e:

            logger.error(
                f"Erreur AI : {e}"
            )

            return JsonResponse(
                {
                    "error": str(e)
                },
                status=500
            )

    return render(
        request,
        "dashboard/ai_assistant.html"
    )


# ============================================================
# ACTIVITE COMMERCIALE
# ============================================================

@approved_required
def activite_create(request):

    departements = [
        str(i).zfill(2)
        for i in range(1, 93)
    ]

    mois = range(1, 13)

    annees = [2024, 2025]

    if request.method == "POST":

        ville = request.POST["ville"]
        annee = request.POST["annee"]
        mois_value = request.POST["mois"]

        existe = (
            ActiviteCommerciale.objects
            .filter(
                ville=ville,
                annee=annee,
                mois=mois_value
            )
            .exists()
        )

        if existe:

            messages.error(
                request,
                "Une activité existe déjà pour cette ville, cette année et ce mois."
            )

            return render(
                request,
                "dashboard/activite_form.html",
                {
                    "departements": departements,
                    "mois": mois,
                    "annees": annees
                }
            )

        ActiviteCommerciale.objects.create(
            code_dept=request.POST["code_dept"],
            bv2022=request.POST["bv2022"],
            ville=ville,
            ca_tot=request.POST["ca_tot"],
            mois=mois_value,
            annee=annee
        )

        messages.success(
            request,
            "Activité commerciale ajoutée avec succès."
        )

        return redirect("activite_list")

    return render(
        request,
        "dashboard/activite_form.html",
        {
            "departements": departements,
            "mois": mois,
            "annees": annees
        }
    )


@approved_required
def activite_list(request):

    activites = ActiviteCommerciale.objects.all()

    return render(
        request,
        "dashboard/activite_list.html",
        {
            "activites": activites
        }
    )


@approved_required
def activite_update(request, id):

    activite = get_object_or_404(
        ActiviteCommerciale,
        id=id
    )

    departements = [
        str(i).zfill(2)
        for i in range(1, 93)
    ]

    mois = range(1, 13)

    annees = [2024, 2025]

    if request.method == "POST":

        activite.code_dept = request.POST["code_dept"]
        activite.bv2022 = request.POST["bv2022"]
        activite.ville = request.POST["ville"]
        activite.ca_tot = request.POST["ca_tot"]
        activite.mois = request.POST["mois"]
        activite.annee = request.POST["annee"]

        activite.save()

        messages.success(
            request,
            "Activité commerciale modifiée."
        )

        return redirect("activite_list")

    return render(
        request,
        "dashboard/activite_form.html",
        {
            "activite": activite,
            "departements": departements,
            "mois": mois,
            "annees": annees
        }
    )


@approved_required
def activite_delete(request, id):

    activite = get_object_or_404(
        ActiviteCommerciale,
        id=id
    )

    if request.method == "POST":

        activite.delete()

        messages.success(
            request,
            "Activité commerciale supprimée."
        )

        return redirect("activite_list")

    return render(
        request,
        "dashboard/activite_delete.html",
        {
            "activite": activite
        }
    )