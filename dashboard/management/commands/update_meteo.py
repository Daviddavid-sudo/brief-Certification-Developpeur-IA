from django.core.management.base import BaseCommand
from dashboard.models import MeteoArchive
import requests
from datetime import datetime

class Command(BaseCommand):
    help = 'Récupère l’historique météo complet de l’année 2025 pour les villes cibles'

    def handle(self, *args, **options):
        # Configuration des villes
        villes = {
            "Paris": {"lat": 48.8566, "lon": 2.3522},
            "Lille": {"lat": 50.6292, "lon": 3.0573},
            "Marseille": {"lat": 43.2965, "lon": 5.3698}
        }

        # URL de l'API Archive (indispensable pour les dates passées)
        url = "https://archive-api.open-meteo.com/v1/archive"

        for ville, coords in villes.items():
            self.stdout.write(f"⏳ Récupération des données 2025 pour : {ville}...")
            
            params = {
                "latitude": coords["lat"],
                "longitude": coords["lon"],
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
                "daily": "temperature_2m_max,temperature_2m_min",
                "timezone": "auto"
            }
            
            try:
                response = requests.get(url, params=params)
                data = response.json()
                
                # Extraction des listes de l'API
                dates = data['daily']['time']
                t_max_list = data['daily']['temperature_2m_max']
                t_min_list = data['daily']['temperature_2m_min']

                nb_jours_crees = 0
                
                # On parcourt chaque jour de la liste renvoyée par l'API
                for i in range(len(dates)):
                    # On ignore les jours où les données sont absentes (ex: futur)
                    if t_max_list[i] is not None and t_min_list[i] is not None:
                        dt = datetime.strptime(dates[i], "%Y-%m-%d")
                        
                        # Enregistrement dans la base de données Django
                        obj, created = MeteoArchive.objects.update_or_create(
                            ville=ville, 
                            annee=dt.year, 
                            mois=dt.month, 
                            jour=dt.day,
                            defaults={
                                'temp_max': t_max_list[i], 
                                'temp_min': t_min_list[i]
                            }
                        )
                        nb_jours_crees += 1

                self.stdout.write(self.style.SUCCESS(f"✅ {ville} terminé : {nb_jours_crees} jours enregistrés."))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erreur lors de la récupération pour {ville}: {e}"))

        self.stdout.write(self.style.SUCCESS("\n🚀 Mise à jour globale terminée !"))