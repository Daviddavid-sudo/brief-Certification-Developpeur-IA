from django.core.management.base import BaseCommand
from dashboard.models import MeteoArchive
import requests
from datetime import datetime

class Command(BaseCommand):
    help = 'Récupère la météo du jour et l’enregistre dans la DB'

    def handle(self, *args, **options):
        villes = {
            "Paris": {"lat": 48.8566, "lon": 2.3522},
            "Lille": {"lat": 50.6292, "lon": 3.0573},
            "Marseille": {"lat": 43.2965, "lon": 5.3698}
        }

        for ville, coords in villes.items():
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": coords["lat"],
                "longitude": coords["lon"],
                "daily": "temperature_2m_max,temperature_2m_min",
                "timezone": "auto"
            }
            
            try:
                response = requests.get(url, params=params)
                data = response.json()
                date_str = data['daily']['time'][0]
                t_max = data['daily']['temperature_2m_max'][0]
                t_min = data['daily']['temperature_2m_min'][0]
                dt = datetime.strptime(date_str, "%Y-%m-%d")

                MeteoArchive.objects.update_or_create(
                    ville=ville, annee=dt.year, mois=dt.month, jour=dt.day,
                    defaults={'temp_max': t_max, 'temp_min': t_min}
                )
                self.stdout.write(self.style.SUCCESS(f"✅ {ville} mis à jour"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erreur {ville}: {e}"))