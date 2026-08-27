import base64
import io
import json
import logging
import os

import geopandas as gpd
import matplotlib
import pandas as pd

matplotlib.use("Agg")

from datetime import datetime

import matplotlib.pyplot as plt
import plotly.graph_objects as go
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.db import connection
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from dashboard.services import (
    ask_llm_about_db,
    execute_ai_sql,
)

from .models import (
    ActiviteCommerciale,
    MeteoArchive,
    Population,
    UserProfile,
)

# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger("ai_monitoring")


# ============================================================
# LANDING PAGE
# ============================================================

def landing_page(request):

    return render(
        request,
        "dashboard/landing.html"
    )


# ============================================================
# AUTHENTIFICATION
# ============================================================

class CustomLoginView(LoginView):

    template_name = "dashboard/login.html"

    redirect_authenticated_user = True

    def get_success_url(self):

        user = self.request.user

        if user.is_staff:
            return "/carte/"

        if hasattr(user, "profile") and user.profile.is_approved:
            return "/carte/"

        return "/meteo_calendrier/"


def is_admin(user):

    return (
        user.is_authenticated
        and user.is_staff
    )


def approved_required(view_func):

    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:

            return redirect("login")

        if request.user.is_staff:

            return view_func(
                request,
                *args,
                **kwargs
            )

        if not hasattr(request.user, "profile"):

            messages.warning(
                request,
                "Votre compte est en attente d'approbation."
            )

            return redirect("meteo_calendrier")

        if not request.user.profile.is_approved:

            messages.warning(
                request,
                "Votre compte est en attente d'approbation."
            )

            return redirect("meteo_calendrier")

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


def register(request):

    if request.method == "POST":

        form = UserCreationForm(
            request.POST
        )

        if form.is_valid():

            user = form.save()

            UserProfile.objects.create(
                user=user,
                is_approved=False
            )

            login(
                request,
                user
            )

            return redirect(
                "meteo_calendrier"
            )

    else:

        form = UserCreationForm()

    return render(
        request,
        "dashboard/register/register.html",
        {
            "form": form
        }
    )


# ============================================================
# ADMINISTRATION DES UTILISATEURS
# ============================================================

def users_view(request):

    if not request.user.is_authenticated:

        return redirect("login")

    if not request.user.is_staff:

        messages.error(
            request,
            "Vous n'avez pas accès à cette page."
        )

        return redirect("meteo_calendrier")

    users = (
        User.objects
        .select_related("profile")
        .order_by("-date_joined")
    )

    return render(
        request,
        "dashboard/users.html",
        {
            "users": users
        }
    )


@require_POST
def approve_user(request, user_id):

    if not request.user.is_authenticated:

        return redirect("login")

    if not request.user.is_staff:

        messages.error(
            request,
            "Accès refusé."
        )

        return redirect("meteo_calendrier")

    user = get_object_or_404(
        User,
        id=user_id
    )

    if user == request.user:

        messages.error(
            request,
            "Vous ne pouvez pas modifier votre propre compte."
        )

        return redirect("users")

    profile, created = UserProfile.objects.get_or_create(
        user=user
    )

    profile.is_approved = True

    profile.save()

    messages.success(
        request,
        f"Le compte de {user.username} a été approuvé."
    )

    return redirect("users")


@require_POST
def reject_user(request, user_id):

    if not request.user.is_authenticated:

        return redirect("login")

    if not request.user.is_staff:

        messages.error(
            request,
            "Accès refusé."
        )

        return redirect("meteo_calendrier")

    user = get_object_or_404(
        User,
        id=user_id
    )

    if user == request.user:

        messages.error(
            request,
            "Vous ne pouvez pas modifier votre propre compte."
        )

        return redirect("users")

    profile, created = UserProfile.objects.get_or_create(
        user=user
    )

    profile.is_approved = False

    profile.save()

    messages.success(
        request,
        f"Le compte de {user.username} n'est plus approuvé."
    )

    return redirect("users")


# ============================================================
# MONITORING
# ============================================================

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

    status_code = (
        200
        if is_healthy
        else 503
    )

    return JsonResponse(
        {
            "status":
                "healthy"
                if is_healthy
                else "unhealthy",

            "timestamp":
                datetime.now().isoformat(),

            "components":
                checks
        },
        status=status_code
    )


# ============================================================
# UTILITAIRE CARTE MATPLOTLIB
# ============================================================

def get_plot_uri():

    buf = io.BytesIO()

    plt.savefig(
        buf,
        format="png",
        bbox_inches="tight",
        dpi=120
    )

    buf.seek(0)

    uri = base64.b64encode(
        buf.read()
    ).decode("utf-8")

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
# + GRAPHIQUE ÉVOLUTION DU CA
# ============================================================

@approved_required
def carte_ventes_view(request):

    # ========================================================
    # CONFIGURATION
    # ========================================================

    selected_year = 2024

    selected_month = request.GET.get(
        "month",
        timezone.now().month
    )

    try:

        selected_month = int(selected_month)

    except (TypeError, ValueError):

        selected_month = 1

    if selected_month < 1 or selected_month > 12:

        selected_month = 1


    mois_noms = [
        "Janvier",
        "Février",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Août",
        "Septembre",
        "Octobre",
        "Novembre",
        "Décembre",
    ]


    # ========================================================
    # GEOJSON
    # ========================================================

    path_geojson = os.path.join(
        settings.BASE_DIR,
        "data",
        "departements.geojson"
    )

    france = gpd.read_file(
        path_geojson
    )

    france["code"] = (
        france["code"]
        .astype(str)
        .str.strip()
    )


    # ========================================================
    # VENTES DU MOIS
    # ========================================================

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


    # ========================================================
    # VALEURS PAR DÉFAUT
    # ========================================================

    top_departements = []

    total_ca = 0

    nombre_departements = 0

    top_department = "—"

    top_department_ca = 0

    ca_moyen = 0


    # ========================================================
    # AGRÉGATION DES VENTES
    # ========================================================

    df_regroupe = pd.DataFrame(
        columns=[
            "code_dept",
            "ca_tot"
        ]
    )


    if not df_ventes.empty:

        df_ventes["code_dept"] = (
            df_ventes["code_dept"]
            .astype(str)
            .str.strip()
        )

        df_ventes["ca_tot"] = pd.to_numeric(
            df_ventes["ca_tot"],
            errors="coerce"
        ).fillna(0)


        df_regroupe = (
            df_ventes
            .groupby(
                "code_dept",
                as_index=False
            )["ca_tot"]
            .sum()
            .sort_values(
                "ca_tot",
                ascending=False
            )
        )


        # ====================================================
        # KPI
        # ====================================================

        total_ca = float(
            df_regroupe["ca_tot"].sum()
        )

        nombre_departements = int(
            df_regroupe["code_dept"].nunique()
        )

        if nombre_departements > 0:

            ca_moyen = (
                total_ca
                / nombre_departements
            )


        # ====================================================
        # TOP 10
        # ====================================================

        top10 = (
            df_regroupe
            .head(10)
            .reset_index(drop=True)
        )


        for index, row in top10.iterrows():

            code = str(
                row["code_dept"]
            ).strip()

            nom = code


            try:

                departement_geo = france[
                    france["code"] == code
                ]

                if not departement_geo.empty:

                    if "nom" in france.columns:

                        nom = (
                            departement_geo
                            .iloc[0]["nom"]
                        )

                    elif "name" in france.columns:

                        nom = (
                            departement_geo
                            .iloc[0]["name"]
                        )

            except Exception as e:

                logger.warning(
                    f"Impossible de trouver "
                    f"le département {code}: {e}"
                )


            top_departements.append(
                {
                    "rang":
                        index + 1,

                    "code":
                        code,

                    "nom":
                        nom,

                    "ca":
                        float(row["ca_tot"])
                }
            )


        # ====================================================
        # MEILLEUR DÉPARTEMENT
        # ====================================================

        if top_departements:

            top_department = (
                top_departements[0]["nom"]
            )

            top_department_ca = (
                top_departements[0]["ca"]
            )


    # ========================================================
    # CARTE
    # ========================================================

    fig_map, ax = plt.subplots(
        figsize=(10, 10)
    )


    if not df_regroupe.empty:

        france_map = france.merge(
            df_regroupe,
            left_on="code",
            right_on="code_dept",
            how="left"
        )


        vmax = float(
            df_regroupe["ca_tot"].max()
        )

        if vmax <= 0:

            vmax = 1


        france_map.plot(
            column="ca_tot",
            ax=ax,
            legend=True,
            cmap="OrRd",
            vmin=0,
            vmax=vmax,
            missing_kwds={
                "color": "#eeeeee",
                "edgecolor": "white"
            },
            legend_kwds={
                "label":
                    "Chiffre d'affaires (€)"
            }
        )


    else:

        france.plot(
            ax=ax,
            color="#eeeeee",
            edgecolor="white"
        )


    ax.set_axis_off()

    ax.set_title(
        f"Chiffre d'affaires par département — "
        f"{mois_noms[selected_month - 1]} {selected_year}",
        fontsize=16,
        fontweight="bold"
    )


    # ========================================================
    # CONVERSION CARTE → BASE64
    # ========================================================

    map_buffer = io.BytesIO()

    fig_map.savefig(
        map_buffer,
        format="png",
        bbox_inches="tight",
        dpi=120
    )

    map_buffer.seek(0)

    data_map = base64.b64encode(
        map_buffer.read()
    ).decode("utf-8")

    plt.close(fig_map)


    # ========================================================
    # ÉVOLUTION DU CA SUR L'ANNÉE
    # ========================================================

    evolution_qs = (
        ActiviteCommerciale.objects
        .filter(
            annee=selected_year
        )
        .values("mois")
        .annotate(
            total_ca=Sum("ca_tot")
        )
        .order_by("mois")
    )


    ca_par_mois = {
        int(row["mois"]):
            float(row["total_ca"] or 0)

        for row in evolution_qs
    }


    # Toujours les 12 mois

    ca_evolution = [
        ca_par_mois.get(
            mois_num,
            0
        )

        for mois_num in range(1, 13)
    ]


    # ========================================================
    # GRAPHIQUE PLOTLY
    # ========================================================

    fig_evolution = go.Figure()


    fig_evolution.add_trace(
        go.Scatter(
            x=mois_noms,

            y=ca_evolution,

            mode="lines+markers",

            name="Chiffre d'affaires",

            line=dict(
                width=3,
                shape="spline"
            ),

            marker=dict(
                size=7
            ),

            hovertemplate=(
                "<b>%{x}</b><br>"
                "CA : %{y:,.0f} €"
                "<extra></extra>"
            ),
        )
    )


    # ========================================================
    # LIGNE DU MOIS SÉLECTIONNÉ
    # ========================================================

    fig_evolution.add_vline(
        x=selected_month - 1,
        line_width=1,
        line_dash="dash",
        opacity=0.5
    )


    # ========================================================
    # STYLE DU GRAPHIQUE
    # ========================================================

    fig_evolution.update_layout(

        title={
            "text":
                "Évolution du chiffre d'affaires — 2024",

            "x":
                0.02,

            "xanchor":
                "left",

            "font": {
                "size": 16
            }
        },

        xaxis={
            "title": "Mois",
            "showgrid": False
        },

        yaxis={
            "title": "Chiffre d'affaires (€)",
            "separatethousands": True
        },

        hovermode="x unified",

        template="plotly_white",

        height=420,

        margin={
            "l": 60,
            "r": 30,
            "t": 65,
            "b": 55
        },

        font={
            "family": "Arial",
            "size": 12
        },

        paper_bgcolor="white",

        plot_bgcolor="white",

        showlegend=False
    )


    # ========================================================
    # PLOTLY → HTML
    # ========================================================

    graph_html = fig_evolution.to_html(

        full_html=False,

        include_plotlyjs="cdn",

        config={
            "responsive": True,

            "displayModeBar": True,

            "displaylogo": False,

            "modeBarButtonsToRemove": [
                "lasso2d",
                "select2d"
            ]
        }
    )


    # ========================================================
    # CONTEXT → carte.html
    # ========================================================

    context = {

        # CARTE
        "data_map":
            data_map,

        # FILTRE
        "selected_month":
            selected_month,

        "months_range":
            range(1, 13),

        # TOP 10
        "top_departements":
            top_departements,

        # KPI
        "total_ca":
            total_ca,

        "top_department":
            top_department,

        "top_department_ca":
            top_department_ca,

        "ca_moyen":
            ca_moyen,

        "nombre_departements":
            nombre_departements,

        # GRAPHIQUE
        "graph_html":
            graph_html,

        "ca_evolution":
            ca_evolution,

        "mois_noms":
            mois_noms,
    }


    return render(
        request,
        "dashboard/carte.html",
        context
    )


# ============================================================
# METEO
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


            resultats = (
                MeteoArchive.objects
                .filter(
                    annee=dt_obj.year,
                    mois=dt_obj.month,
                    jour=dt_obj.day
                )
            )


            path_geojson = os.path.join(
                settings.BASE_DIR,
                "data",
                "departements.geojson"
            )


            france = gpd.read_file(
                path_geojson
            )


            france["code"] = (
                france["code"]
                .astype(str)
                .str.strip()
            )


            fig, ax = plt.subplots(
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
                    .astype(str)
                    .str.strip()
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
                        "label":
                            "Température minimale (°C)",

                        "orientation":
                            "horizontal",

                        "pad":
                            0.05
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
            "resultats":
                resultats,

            "date_selectionnee":
                date_selectionnee,

            "data_map":
                data_map
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


    france["code"] = (
        france["code"]
        .astype(str)
        .str.strip()
    )


    # ========================================================
    # DONNÉES POPULATION
    # ========================================================

    pop_qs = (
        Population.objects
        .all()
        .values(
            "dep",
            "pop"
        )
    )


    df_pop = pd.DataFrame(
        list(pop_qs)
    )


    population_totale = 0

    top_departements = []


    if not df_pop.empty:

        df_pop["dep"] = (
            df_pop["dep"]
            .astype(str)
            .str.strip()
        )

        df_pop["pop"] = pd.to_numeric(
            df_pop["pop"],
            errors="coerce"
        ).fillna(0)


        population_totale = float(
            df_pop["pop"].sum()
        )


        # ====================================================
        # TOP 10
        # ====================================================

        top10 = (
            df_pop
            .sort_values(
                "pop",
                ascending=False
            )
            .head(10)
            .reset_index(drop=True)
        )


        for index, row in top10.iterrows():

            code = str(
                row["dep"]
            ).strip()

            nom = code


            try:

                departement_geo = france[
                    france["code"] == code
                ]


                if not departement_geo.empty:

                    if "nom" in france.columns:

                        nom = (
                            departement_geo
                            .iloc[0]["nom"]
                        )

                    elif "name" in france.columns:

                        nom = (
                            departement_geo
                            .iloc[0]["name"]
                        )

            except Exception:

                pass


            top_departements.append(
                {
                    "rang":
                        index + 1,

                    "code":
                        code,

                    "nom":
                        nom,

                    "population":
                        float(row["pop"])
                }
            )


    # ========================================================
    # CARTE
    # ========================================================

    fig, ax = plt.subplots(
        figsize=(10, 10)
    )


    if not df_pop.empty:

        france_map = france.merge(
            df_pop,
            left_on="code",
            right_on="dep",
            how="left"
        )


        france_map.plot(
            column="pop",
            ax=ax,
            legend=True,
            cmap="YlGnBu",
            missing_kwds={
                "color": "#f5f5f5"
            },
            legend_kwds={
                "label":
                    "Nombre d'habitants (Source INSEE)"
            }
        )


    else:

        france.plot(
            ax=ax,
            color="lightgrey",
            edgecolor="white"
        )


    ax.set_axis_off()


    ax.set_title(
        "Population par département",
        fontsize=16,
        fontweight="bold"
    )


    data_map = get_plot_uri()


    return render(
        request,
        "dashboard/population.html",
        {
            "data_map":
                data_map,

            "population_totale":
                population_totale,

            "top_departements":
                top_departements
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
            .get(
                "message",
                ""
            )
            .strip()
        )


        logger.info(
            f"Requête utilisateur reçue : "
            f"{user_query}"
        )


        try:

            ai_raw_output = (
                ask_llm_about_db(
                    user_query
                )
            )


            db_data = (
                execute_ai_sql(
                    ai_raw_output
                )
            )


            if (
                isinstance(
                    db_data,
                    dict
                )
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

                    for row
                    in db_data["rows"][:3]
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

                final_response = (
                    ai_raw_output
                )


            return JsonResponse(
                {
                    "response":
                        final_response
                }
            )


        except Exception as e:

            logger.error(
                f"Erreur AI : {e}"
            )


            return JsonResponse(
                {
                    "error":
                        str(e)
                },
                status=500
            )


    return render(
        request,
        "dashboard/ai_assistant.html"
    )


# ============================================================
# ACTIVITÉ COMMERCIALE - CRÉATION
# ============================================================

@approved_required
def activite_create(request):

    departements = [
        str(i).zfill(2)
        for i in range(1, 93)
    ]

    mois = range(1, 13)

    annees = [
        2024,
        2025
    ]


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
                "Une activité existe déjà pour cette ville, "
                "cette année et ce mois."
            )


            return render(
                request,
                "dashboard/activite_form.html",
                {
                    "departements":
                        departements,

                    "mois":
                        mois,

                    "annees":
                        annees
                }
            )


        ActiviteCommerciale.objects.create(

            code_dept=
                request.POST["code_dept"],

            bv2022=
                request.POST["bv2022"],

            ville=
                ville,

            ca_tot=
                request.POST["ca_tot"],

            mois=
                mois_value,

            annee=
                annee
        )


        messages.success(
            request,
            "Activité commerciale ajoutée avec succès."
        )


        return redirect(
            "activite_list"
        )


    return render(
        request,
        "dashboard/activite_form.html",
        {
            "departements":
                departements,

            "mois":
                mois,

            "annees":
                annees
        }
    )


# ============================================================
# ACTIVITÉ COMMERCIALE - LISTE
# ============================================================

@approved_required
def activite_list(request):

    search = (
        request.GET
        .get("search", "")
        .strip()
    )


    activites = (
        ActiviteCommerciale.objects
        .all()
        .order_by(
            "-annee",
            "-mois",
            "ville"
        )
    )


    if search:

        activites = activites.filter(
            Q(ville__icontains=search)
            |
            Q(code_dept__icontains=search)
        )


    return render(
        request,
        "dashboard/activite_list.html",
        {
            "activites":
                activites,

            "search":
                search
        }
    )


# ============================================================
# ACTIVITÉ COMMERCIALE - MODIFICATION
# ============================================================

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

    annees = [
        2024,
        2025
    ]


    if request.method == "POST":

        activite.code_dept = (
            request.POST["code_dept"]
        )

        activite.bv2022 = (
            request.POST["bv2022"]
        )

        activite.ville = (
            request.POST["ville"]
        )

        activite.ca_tot = (
            request.POST["ca_tot"]
        )

        activite.mois = (
            request.POST["mois"]
        )

        activite.annee = (
            request.POST["annee"]
        )


        activite.save()


        messages.success(
            request,
            "Activité commerciale modifiée."
        )


        return redirect(
            "activite_list"
        )


    return render(
        request,
        "dashboard/activite_form.html",
        {
            "activite":
                activite,

            "departements":
                departements,

            "mois":
                mois,

            "annees":
                annees
        }
    )


# ============================================================
# ACTIVITÉ COMMERCIALE - SUPPRESSION
# ============================================================

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


        return redirect(
            "activite_list"
        )


    return render(
        request,
        "dashboard/activite_delete.html",
        {
            "activite":
                activite
        }
    )