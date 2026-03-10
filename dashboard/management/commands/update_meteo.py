import requests
import time
from datetime import datetime
from django.core.management.base import BaseCommand
from dashboard.models import MeteoArchive
from django.db import transaction

class Command(BaseCommand):
    help = 'Récupère la météo pour TOUTE l\'année 2025'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("🧹 Vidage de la table pour une mise à jour complète..."))
        MeteoArchive.objects.all().delete()

        # Coordonnées (On garde les mêmes que précédemment)
        COORDS = {
            "01": (46.1, 5.2), "02": (49.5, 3.5), "03": (46.4, 3.3), "04": (44.1, 6.2),
            "05": (44.6, 6.3), "06": (43.9, 7.2), "07": (44.7, 4.5), "08": (49.5, 4.7),
            "09": (42.9, 1.5), "10": (48.3, 4.1), "11": (43.1, 2.4), "12": (44.3, 2.5),
            "13": (43.5, 5.0), "14": (49.1, -0.3), "15": (45.0, 2.7), "16": (45.7, 0.2),
            "17": (45.7, -0.6), "18": (47.1, 2.4), "19": (45.3, 1.7), "21": (47.3, 4.8),
            "22": (48.5, -2.8), "23": (46.1, 2.0), "24": (45.1, 0.7), "25": (47.1, 6.3),
            "26": (44.7, 5.2), "27": (49.1, 1.1), "28": (48.4, 1.4), "29": (48.3, -4.1),
            "2A": (41.9, 9.0), "2B": (42.4, 9.3), "30": (44.0, 4.1), "31": (43.5, 1.4),
            "32": (43.7, 0.6), "33": (44.8, -0.6), "34": (43.6, 3.2), "35": (48.2, -1.7),
            "36": (46.8, 1.6), "37": (47.3, 0.7), "38": (45.3, 5.4), "39": (46.7, 5.6),
            "40": (43.9, -0.7), "41": (47.6, 1.3), "42": (45.7, 4.2), "43": (45.1, 3.9),
            "44": (47.4, -1.7), "45": (47.9, 2.3), "46": (44.6, 1.6), "47": (44.3, 0.5),
            "48": (44.5, 3.5), "49": (47.4, -0.6), "50": (49.1, -1.1), "51": (48.9, 4.2),
            "52": (48.1, 5.2), "53": (48.1, -0.7), "54": (48.7, 6.1), "55": (49.0, 5.4),
            "56": (47.9, -2.7), "57": (49.0, 6.7), "58": (47.0, 3.5), "59": (50.5, 3.2),
            "60": (49.4, 2.4), "61": (48.6, 0.1), "62": (50.5, 2.4), "63": (45.7, 3.2),
            "64": (43.3, -0.8), "65": (43.0, 0.1), "66": (42.6, 2.5), "67": (48.6, 7.5),
            "68": (47.9, 7.3), "69": (45.9, 4.7), "70": (47.6, 6.0), "71": (46.6, 4.4),
            "72": (48.0, 0.2), "73": (45.5, 6.3), "74": (46.0, 6.3), "75": (48.8, 2.3),
            "76": (49.6, 1.0), "77": (48.6, 2.9), "78": (48.8, 1.8), "79": (46.5, -0.3),
            "80": (49.9, 2.3), "81": (43.7, 2.2), "82": (44.1, 1.3), "83": (43.5, 6.3),
            "84": (43.9, 5.1), "85": (46.7, -1.3), "86": (46.6, 0.4), "87": (45.9, 1.2),
            "88": (48.2, 6.5), "89": (47.8, 3.6), "90": (47.6, 6.9), "91": (48.5, 2.2),
            "92": (48.8, 2.2), "93": (48.9, 2.4), "94": (48.8, 2.4), "95": (49.1, 2.2),
            "971": (16.2, -61.5), "972": (14.6, -61.0), "973": (4.0, -53.0), "974": (-21.1, 55.5)
        }

        url_archive = "https://archive-api.open-meteo.com/v1/archive"

        self.stdout.write(f"⏳ Récupération de 365 jours pour {len(COORDS)} départements...")

        for code, (lat, lon) in COORDS.items():
            try:
                params = {
                    "latitude": lat, "longitude": lon,
                    "start_date": "2025-01-01", 
                    "end_date": "2025-12-31", # <--- C'est ici qu'on demande toute l'année
                    "daily": "temperature_2m_max,temperature_2m_min", "timezone": "auto"
                }
                res = requests.get(url_archive, params=params).json()
                
                if 'daily' in res:
                    meteo_objs = []
                    dates = res['daily']['time']
                    t_max = res['daily']['temperature_2m_max']
                    t_min = res['daily']['temperature_2m_min']

                    for i in range(len(dates)):
                        dt = datetime.strptime(dates[i], "%Y-%m-%d")
                        meteo_objs.append(MeteoArchive(
                            dep=code,
                            annee=dt.year, mois=dt.month, jour=dt.day,
                            temp_max=t_max[i] if t_max[i] is not None else 0,
                            temp_min=t_min[i] if t_min[i] is not None else 0
                        ))
                    
                    with transaction.atomic():
                        MeteoArchive.objects.bulk_create(meteo_objs, ignore_conflicts=True)
                    
                    self.stdout.write(self.style.SUCCESS(f"✅ Code {code} importé (365 jours)"))
                
                # Petite pause pour respecter l'API
                time.sleep(0.1)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erreur {code}: {e}"))

        self.stdout.write(self.style.SUCCESS("\n🚀 Année 2025 complète et prête !"))