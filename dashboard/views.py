import os
import io
import urllib, base64
import pandas as pd
import geopandas as gpd
import matplotlib
import logging
from datetime import datetime
from django.utils import timezone

# Configure Matplotlib for server-side rendering
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from .models import ActiviteCommerciale, MeteoArchive, Population
from dashboard.services import ask_llm_about_db, execute_ai_sql

# Setup Monitoring Logger
logger = logging.getLogger('ai_monitoring')

# --- UTILS ---
def get_plot_uri():
    """Converts Matplotlib plots to URI strings for HTML display."""
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    uri = urllib.parse.quote(base64.b64encode(buf.read()))
    plt.close()
    return uri

# --- VUE 1 : VENTES (CARTE) ---
def carte_ventes_view(request):
    selected_year = 2024 
    selected_month = request.GET.get('month', timezone.now().month)

    path_geojson = os.path.join(settings.BASE_DIR, 'data', 'departements.geojson')
    france = gpd.read_file(path_geojson)

    ventes_qs = ActiviteCommerciale.objects.filter(
        mois=selected_month, 
        annee=selected_year
    ).values('code_dept', 'ca_tot')
    
    df_ventes = pd.DataFrame(list(ventes_qs))

    # Fixed Scale Logic for stability
    max_pop_obj = Population.objects.order_by('-pop').first()
    vmax_fixed = (max_pop_obj.pop * 6) if max_pop_obj else 1000000

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    
    if not df_ventes.empty:
        df_regroupe = df_ventes.groupby('code_dept')['ca_tot'].sum().reset_index()
        france = france.merge(df_regroupe, left_on='code', right_on='code_dept', how='left')
        
        france.plot(
            column='ca_tot', 
            ax=ax, 
            legend=True, 
            cmap='OrRd', 
            vmin=0,           
            vmax=vmax_fixed,  
            missing_kwds={'color': 'lightgrey'}, 
            legend_kwds={'label': "Chiffre d'Affaires (€)"}
        )
    else:
        france.plot(ax=ax, color='lightgrey')

    ax.set_axis_off()
    ax.set_title(f"Ventes par Département - Mois {selected_month}")
    
    return render(request, 'dashboard/carte.html', {
        'data_map': get_plot_uri(),
        'selected_month': int(selected_month),
        'months_range': range(1, 13)
    })

# --- VUE 2 : MÉTÉO ---
def consultation_meteo(request):
    resultats = None
    data_map = None
    date_selectionnee = request.GET.get('date_choisie')

    if date_selectionnee:
        try:
            dt_obj = datetime.strptime(date_selectionnee, "%Y-%m-%d")
            resultats = MeteoArchive.objects.filter(
                annee=dt_obj.year, 
                mois=dt_obj.month, 
                jour=dt_obj.day
            )
            
            path_geojson = os.path.join(settings.BASE_DIR, 'data', 'departements.geojson')
            france = gpd.read_file(path_geojson)
            fig, ax = plt.subplots(1, 1, figsize=(10, 10))

            if resultats.exists():
                df_meteo = pd.DataFrame(list(resultats.values('dep', 'temp_min', 'temp_max')))
                df_meteo['dep'] = df_meteo['dep'].apply(lambda x: x.zfill(2) if (len(x) == 1 and x.isdigit()) else x)
                france = france.merge(df_meteo, left_on='code', right_on='dep', how='left')

                france.plot(
                    column='temp_min', 
                    ax=ax, 
                    legend=True, 
                    cmap='coolwarm',
                    missing_kwds={'color': '#f0f0f0'}, 
                    legend_kwds={'label': "Température Minimale (°C)", 'orientation': "horizontal", 'pad': 0.05}
                )
            else:
                france.plot(ax=ax, color='#f0f0f0', edgecolor='white')

            ax.set_axis_off()
            ax.set_title(f"Météo France - {dt_obj.strftime('%d/%m/%Y')}")
            data_map = get_plot_uri()
        except Exception as e:
            logger.error(f"Erreur Carte Météo: {e}")

    return render(request, 'dashboard/meteo_calendrier.html', {
        'resultats': resultats,
        'date_selectionnee': date_selectionnee,
        'data_map': data_map
    })

# --- VUE 3 : POPULATION ---
def carte_population_view(request):
    path_geojson = os.path.join(settings.BASE_DIR, 'data', 'departements.geojson')
    france = gpd.read_file(path_geojson)
    pop_qs = Population.objects.all().values('dep', 'pop')
    df_pop = pd.DataFrame(list(pop_qs))

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    if not df_pop.empty:
        france = france.merge(df_pop, left_on='code', right_on='dep', how='left')
        france.plot(column='pop', ax=ax, legend=True, cmap='YlGnBu', 
                    missing_kwds={'color': '#f5f5f5'}, 
                    legend_kwds={'label': "Nombre d'habitants (Source INSEE)"})
    else:
        france.plot(ax=ax, color='lightgrey')

    ax.set_axis_off()
    ax.set_title("Population réelle par Département")
    return render(request, 'dashboard/population.html', {'data_map': get_plot_uri()})

# --- VUE 4 : ASSISTANT IA (AVEC MONITORAGE) ---
def ai_assistant_view(request):
    """
    Main entry point for the AI Assistant.
    Satisfies: AI Integration, Monitoring, and Security (OWASP).
    """
    if request.method == "POST":
        user_query = request.POST.get('message', '').strip()
        
        # Log the start of the request (Monitoring)
        logger.info(f"Requête utilisateur reçue: {user_query}")

        # 1. Get the AI's Analysis (Thought process + SQL)
        ai_raw_output = ask_llm_about_db(user_query)
        
        # 2. Extract and execute SQL safely (Security Check)
        db_data = execute_ai_sql(ai_raw_output)
        
        # 3. Final Formatting
        if isinstance(db_data, dict) and db_data['rows']:
            cols = ", ".join(db_data['columns'])
            # Formatting rows for better readability
            formatted_rows = [str(dict(zip(db_data['columns'], row))) for row in db_data['rows'][:3]]
            data_str = " | ".join(formatted_rows)
            final_response = f"J'ai analysé les données. Voici les résultats ({cols}) : {data_str}"
        else:
            # Fallback to the natural language response from the AI
            final_response = ai_raw_output

        return JsonResponse({'response': final_response})

    return render(request, 'dashboard/ai_assistant.html')