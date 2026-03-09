import os
import django

# 1. On dit à ce script d'utiliser les réglages de ton projet Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mon_projet.settings')
django.setup()

from dashboard.models import ActiviteCommerciale

def remplir_ventes_dans_django():
    # Données de test
    ventes = [
        {"ville": "Paris", "code_dept": "75", "ca_tot": 52000, "mois": 3, "annee": 2024, "bv2022": "75056"},
        {"ville": "Lille", "code_dept": "59", "ca_tot": 31000, "mois": 3, "annee": 2024, "bv2022": "59350"},
        {"ville": "Marseille", "code_dept": "13", "ca_tot": 45000, "mois": 3, "annee": 2024, "bv2022": "13055"},
    ]

    for data in ventes:
        # On utilise l'ORM Django : magique, ça écrit au bon endroit !
        ActiviteCommerciale.objects.update_or_create(
            ville=data['ville'],
            annee=data['annee'],
            mois=data['mois'],
            defaults={
                'ca_tot': data['ca_tot'],
                'code_dept': data['code_dept'],
                'bv2022': data['bv2022']
            }
        )
    print("✅ Les ventes ont été injectées dans la base Django (db.sqlite3) !")

if __name__ == "__main__":
    remplir_ventes_dans_django()