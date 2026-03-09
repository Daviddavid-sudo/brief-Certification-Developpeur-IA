# seed_data.py
import os
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mon_projet.settings')
django.setup()

from dashboard.models import ActiviteCommerciale

def ajouter_ventes_test():
    ventes = [
        {"ville": "Paris", "code_dept": "75", "ca_tot": 50000, "mois": 3, "annee": 2024, "bv2022": "75056"},
        {"ville": "Lille", "code_dept": "59", "ca_tot": 35000, "mois": 3, "annee": 2024, "bv2022": "59350"},
        {"ville": "Marseille", "code_dept": "13", "ca_tot": 42000, "mois": 3, "annee": 2024, "bv2022": "13055"},
        {"ville": "Lyon", "code_dept": "69", "ca_tot": 28000, "mois": 3, "annee": 2024, "bv2022": "69123"},
    ]

    for data in ventes:
        obj, created = ActiviteCommerciale.objects.update_or_create(
            ville=data['ville'],
            annee=data['annee'],
            mois=data['mois'],
            defaults={
                'ca_tot': data['ca_tot'],
                'code_dept': data['code_dept'],
                'bv2022': data['bv2022']
            }
        )
        print(f"✅ Données pour {data['ville']} ajoutées.")

if __name__ == "__main__":
    ajouter_ventes_test()