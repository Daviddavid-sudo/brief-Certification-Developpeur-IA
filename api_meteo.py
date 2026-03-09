import requests
import sqlite3
from datetime import datetime

VILLES = {
    "Paris": {"lat": 48.8566, "lon": 2.3522},
    "Lille": {"lat": 50.6292, "lon": 3.0573},
    "Marseille": {"lat": 43.2965, "lon": 5.3698}
}

def initialiser_db():
    conn = sqlite3.connect('meteo_complete.db')
    cursor = conn.cursor()
    # Création de la table avec les nouvelles colonnes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS archives_meteo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ville TEXT,
            annee INTEGER,
            mois INTEGER,
            jour INTEGER,
            temp_max REAL,
            temp_min REAL,
            unite TEXT
        )
    ''')
    conn.commit()
    return conn

def enregistrer_donnees_journalieres():
    conn = initialiser_db()
    cursor = conn.cursor()
    
    for ville, coords in VILLES.items():
        # On demande les données 'daily' pour max et min
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
            
            # On récupère les données du jour actuel (index 0 dans la liste daily)
            date_str = data['daily']['time'][0] # Format "2024-05-20"
            t_max = data['daily']['temperature_2m_max'][0]
            t_min = data['daily']['temperature_2m_min'][0]
            
            # Découpage de la date
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            
            cursor.execute('''
                INSERT INTO archives_meteo (ville, annee, mois, jour, temp_max, temp_min, unite)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ville, dt.year, dt.month, dt.day, t_max, t_min, "°C"))
            
            print(f"✅ {ville} ({date_str}) : Max {t_max}°C / Min {t_min}°C")
            
        except Exception as e:
            print(f"❌ Erreur pour {ville}: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    enregistrer_donnees_journalieres()