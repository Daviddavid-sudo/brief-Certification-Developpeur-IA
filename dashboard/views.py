import os
import io
import urllib, base64
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from django.shortcuts import render
from django.conf import settings
from .models import ActiviteCommerciale, MeteoArchive

# --- VUE 1 : CARTE DES VENTES ---
def carte_ventes_view(request):
    path_geojson = os.path.join(settings.BASE_DIR, 'data', 'departements.geojson')
    france = gpd.read_file(path_geojson)

    ventes_qs = ActiviteCommerciale.objects.all().values('code_dept', 'ca_tot')
    df_ventes = pd.DataFrame(list(ventes_qs))

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    
    if not df_ventes.empty:
        df_regroupe = df_ventes.groupby('code_dept')['ca_tot'].sum().reset_index()
        france = france.merge(df_regroupe, left_on='code', right_on='code_dept', how='left')
        france.plot(column='ca_tot', ax=ax, legend=True, cmap='OrRd', 
                    missing_kwds={'color': 'lightgrey'}, legend_kwds={'label': "Chiffre d'Affaires (€)"})
    else:
        france.plot(ax=ax, color='lightgrey')
        ax.annotate("Aucune donnée disponible", xy=(0.5, 0.5), xycoords='axes fraction', ha='center')

    ax.set_axis_off()
    ax.set_title("Répartition du Chiffre d'Affaires par Département")

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    uri = urllib.parse.quote(base64.b64encode(buf.read()))
    plt.close()

    return render(request, 'dashboard/carte.html', {'data_map': uri})


# --- VUE 2 : CALENDRIER MÉTÉO + CARTE THERMIQUE ---
def consultation_meteo(request):
    resultats = None
    data_map = None
    date_selectionnee = request.GET.get('date_choisie')

    if date_selectionnee:
        try:
            annee, mois, jour = map(int, date_selectionnee.split('-'))
            resultats = MeteoArchive.objects.filter(annee=annee, mois=mois, jour=jour)
            
            # Préparation de la carte de France
            path_geojson = os.path.join(settings.BASE_DIR, 'data', 'departements.geojson')
            france = gpd.read_file(path_geojson)
            
            fig, ax = plt.subplots(1, 1, figsize=(8, 8))

            if resultats.exists():
                df_meteo = pd.DataFrame(list(resultats.values('ville', 'temp_min')))
                
                # Mapping Ville -> Code Département
                mapping_villes_dept = {
                    "Paris": "75", "Lille": "59", "Marseille": "13", "Lyon": "69"
                }
                df_meteo['code_dept'] = df_meteo['ville'].map(mapping_villes_dept)

                # Fusion des données météo avec la carte
                france = france.merge(df_meteo, left_on='code', right_on='code_dept', how='left')
                
                # Affichage avec dégradé du bleu au rouge (coolwarm)
                france.plot(column='temp_min', ax=ax, legend=True, cmap='coolwarm',
                            missing_kwds={'color': '#f0f0f0'}, # Gris très clair pour le reste
                            legend_kwds={'label': "Température Minimale (°C)"})
            else:
                # Si pas de données pour cette date, on affiche la carte vide
                france.plot(ax=ax, color='lightgrey')
                ax.annotate("Données météo non disponibles", xy=(0.5, 0.5), xycoords='axes fraction', ha='center')

            ax.set_axis_off()
            ax.set_title(f"Températures en France le {date_selectionnee}")

            # Conversion Image
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            data_map = urllib.parse.quote(base64.b64encode(buf.read()))
            plt.close()

        except (ValueError, TypeError):
            pass

    return render(request, 'dashboard/meteo_calendrier.html', {
        'resultats': resultats,
        'date_selectionnee': date_selectionnee,
        'data_map': data_map
    })