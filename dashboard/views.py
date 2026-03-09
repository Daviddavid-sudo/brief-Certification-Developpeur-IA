import os
import io
import urllib, base64
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from django.shortcuts import render
from django.conf import settings
from .models import ActiviteCommerciale

def carte_ventes_view(request):
    # 1. Charger le GeoJSON des départements
    path_geojson = os.path.join(settings.BASE_DIR, 'data', 'departements.geojson')
    france = gpd.read_file(path_geojson)

    # 2. Récupérer les données de la DB
    ventes_qs = ActiviteCommerciale.objects.all().values('code_dept', 'ca_tot')
    df_ventes = pd.DataFrame(list(ventes_qs))

    # 3. Préparation de la carte
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    
    if not df_ventes.empty:
        # Grouper le CA par département (au cas où on a plusieurs villes par dept)
        df_regroupe = df_ventes.groupby('code_dept')['ca_tot'].sum().reset_index()
        
        # Fusion : 'code' est le nom de la colonne dans le GeoJSON de Grégoire David
        france = france.merge(df_regroupe, left_on='code', right_on='code_dept', how='left')
        
        # Tracer la carte avec les données
        france.plot(column='ca_tot', ax=ax, legend=True, cmap='OrRd', 
                    missing_kwds={'color': 'lightgrey'}, legend_kwds={'label': "Chiffre d'Affaires (€)"})
    else:
        # Tracer une carte grise vide si pas de données
        france.plot(ax=ax, color='lightgrey')
        ax.annotate("Aucune donnée disponible", xy=(0.5, 0.5), xycoords='axes fraction', ha='center')

    ax.set_axis_off()
    ax.set_title("Répartition du Chiffre d'Affaires par Département")

    # 4. Conversion du graphique en image pour HTML
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    plt.close() # Important : ferme la figure pour libérer la mémoire

    return render(request, 'dashboard/carte.html', {'data_map': uri})

from django.shortcuts import render
from .models import MeteoArchive

def consultation_meteo(request):
    resultats = None
    date_selectionnee = request.GET.get('date_choisie') # Récupère la date du calendrier

    if date_selectionnee:
        # La date arrive au format "YYYY-MM-DD"
        # On la découpe pour correspondre à nos champs annee, mois, jour
        annee, mois, jour = map(int, date_selectionnee.split('-'))
        
        # On cherche toutes les villes pour cette date précise
        resultats = MeteoArchive.objects.filter(annee=annee, mois=mois, jour=jour)

    return render(request, 'dashboard/meteo_calendrier.html', {
        'resultats': resultats,
        'date_selectionnee': date_selectionnee
    })