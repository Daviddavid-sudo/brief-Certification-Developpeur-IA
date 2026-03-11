import os
import io
import urllib, base64
import pandas as pd
import geopandas as gpd
import matplotlib
from datetime import datetime
from django.utils import timezone
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from django.shortcuts import render
from django.conf import settings
from .models import ActiviteCommerciale, MeteoArchive, Population
from django.http import JsonResponse
from django.shortcuts import render
from dashboard.services import ask_llm_about_db, execute_ai_sql


# Helper function to convert Matplotlib plots to URI strings
def get_plot_uri():
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    uri = urllib.parse.quote(base64.b64encode(buf.read()))
    plt.close()
    return uri


def carte_ventes_view(request):
    selected_year = 2024 
    selected_month = request.GET.get('month', timezone.now().month)

    path_geojson = os.path.join(settings.BASE_DIR, 'data', 'departements.geojson')
    france = gpd.read_file(path_geojson)

    # 1. Fetch data for the selected month
    ventes_qs = ActiviteCommerciale.objects.filter(
        mois=selected_month, 
        annee=selected_year
    ).values('code_dept', 'ca_tot')
    
    df_ventes = pd.DataFrame(list(ventes_qs))

    # 2. Logic for Fixed Scale:
    # We find the highest possible population and multiply by 6 (2 * 3.0 multiplier)
    # This ensures the scale doesn't "jump" when you change months.
    max_pop = Population.objects.order_by('-pop').first().pop
    vmax_fixed = max_pop * 6  # 2 (base) * 3 (max seasonality)

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    
    if not df_ventes.empty:
        df_regroupe = df_ventes.groupby('code_dept')['ca_tot'].sum().reset_index()
        france = france.merge(df_regroupe, left_on='code', right_on='code_dept', how='left')
        
        # --- THE FIX: vmin and vmax ---
        france.plot(
            column='ca_tot', 
            ax=ax, 
            legend=True, 
            cmap='OrRd', 
            vmin=0,           # Always start at 0
            vmax=vmax_fixed,  # Always end at the theoretical max
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


def consultation_meteo(request):
    resultats = None
    data_map = None
    date_selectionnee = request.GET.get('date_choisie')

    if date_selectionnee:
        try:
            # 1. Conversion de la chaîne de caractères en objet date
            dt_obj = datetime.strptime(date_selectionnee, "%Y-%m-%d")
            
            # 2. Récupération des données filtrées
            resultats = MeteoArchive.objects.filter(
                annee=dt_obj.year, 
                mois=dt_obj.month, 
                jour=dt_obj.day
            )
            
            # 3. Chargement du fond de carte
            path_geojson = os.path.join(settings.BASE_DIR, 'data', 'departements.geojson')
            france = gpd.read_file(path_geojson)
            
            # Configuration de la figure Matplotlib
            fig, ax = plt.subplots(1, 1, figsize=(10, 10))

            if resultats.exists():
                # 4. Préparation des données météo
                df_meteo = pd.DataFrame(list(resultats.values('dep', 'temp_min', 'temp_max')))

                # --- LE FIX CRUCIAL ---
                # On s'assure que le code département a 2 chiffres (ex: '1' -> '01')
                # pour que la fusion avec le GeoJSON fonctionne à 100%
                df_meteo['dep'] = df_meteo['dep'].apply(lambda x: x.zfill(2) if (len(x) == 1 and x.isdigit()) else x)

                # 5. Fusion (Merge) entre la carte et les données
                # Note: Vérifiez si votre GeoJSON utilise 'code' ou 'code_dept'
                france = france.merge(df_meteo, left_on='code', right_on='dep', how='left')

                # 6. Dessin de la carte
                france.plot(
                    column='temp_min', 
                    ax=ax, 
                    legend=True, 
                    cmap='coolwarm',
                    missing_kwds={'color': '#f0f0f0'}, # Gris clair si donnée manquante
                    legend_kwds={
                        'label': "Température Minimale (°C)",
                        'orientation': "horizontal",
                        'pad': 0.05
                    }
                )
                
                # Ajout des étiquettes de température (optionnel)
                # for idx, row in france.iterrows():
                #    if pd.notnull(row['temp_min']):
                #        ax.annotate(text=f"{row['temp_min']}°", xy=row['geometry'].centroid.coords[0], ha='center', fontsize=8)

            else:
                # Si aucune donnée, on affiche la carte vide en gris
                france.plot(ax=ax, color='#f0f0f0', edgecolor='white')
                ax.text(0.5, 0.5, "Aucune donnée pour cette date", transform=ax.transAxes, ha='center', color='red')

            ax.set_axis_off()
            ax.set_title(f"Météo France - {dt_obj.strftime('%d/%m/%Y')}", fontsize=16, pad=20)
            
            # 7. Génération de l'image
            data_map = get_plot_uri()
            plt.close(fig) # Libère la RAM du serveur

        except Exception as e:
            # Debug: Affiche l'erreur précise dans votre console terminal
            print(f"DEBUG ERROR: {e}")
            pass

    return render(request, 'dashboard/meteo_calendrier.html', {
        'resultats': resultats,
        'date_selectionnee': date_selectionnee,
        'data_map': data_map
    })


# --- VUE 3 : POPULATION (RÉELLE INSEE) ---
def carte_population_view(request):
    path_geojson = os.path.join(settings.BASE_DIR, 'data', 'departements.geojson')
    france = gpd.read_file(path_geojson)

    # Récupération des vraies données de la base de données
    pop_qs = Population.objects.all().values('dep', 'pop')
    df_pop = pd.DataFrame(list(pop_qs))

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    
    if not df_pop.empty:
        # Fusion avec le GeoJSON sur les codes département
        france = france.merge(df_pop, left_on='code', right_on='dep', how='left')
        
        france.plot(column='pop', ax=ax, legend=True, cmap='YlGnBu', 
                    missing_kwds={'color': '#f5f5f5'}, 
                    legend_kwds={'label': "Nombre d'habitants (Source INSEE)"})
    else:
        france.plot(ax=ax, color='lightgrey')
        ax.annotate("Base de données vide. Lancez l'importation CSV.", 
                    xy=(0.5, 0.5), xycoords='axes fraction', ha='center')

    ax.set_axis_off()
    ax.set_title("Population réelle par Département")

    return render(request, 'dashboard/population.html', {'data_map': get_plot_uri()})


def ai_assistant_view(request):
    if request.method == "POST":
        user_query = request.POST.get('message', '')
        
        # 1. Get the AI's "Thought" (which includes the SQL)
        ai_raw_output = ask_llm_about_db(user_query)
        
        # 2. Try to execute the SQL found in that output
        db_data = execute_ai_sql(ai_raw_output)
        
        # 3. Format the final response
        if isinstance(db_data, dict):
            # If we got data, format it as a simple string or HTML table
            cols = ", ".join(db_data['columns'])
            rows = " | ".join([str(r) for r in db_data['rows']])
            final_response = f"Résultats ({cols}) : {rows}"
        else:
            final_response = ai_raw_output

        return JsonResponse({'response': final_response})

    return render(request, 'dashboard/ai_assistant.html')