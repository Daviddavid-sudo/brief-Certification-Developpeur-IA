import requests
import sqlite3
from datetime import datetime

VILLES = {
    "Paris": {"lat": 48.8566, "lon": 2.3522},
    "Lille": {"lat": 50.6292, "lon": 3.0573},
    "Marseille": {"lat": 43.2965, "lon": 5.3698}
}

def importer_annee_complete(annee):
    conn = sqlite3.connect('meteo_complete.db')
    cursor = conn.cursor()
    
    # On crée la table avec une contrainte UNIQUE pour éviter les doublons
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS archives_meteo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ville TEXT,
            annee INTEGER,
            mois INTEGER,
            jour INTEGER,
            temp_max REAL,
            temp_min REAL,
            UNIQUE(ville, annee, mois, jour)
        )
    ''')

    for ville, coords in VILLES.items():
        print(f"Importation de {annee} pour {ville}...")
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": coords["lat"], "longitude": coords["lon"],
            "start_date": f"{annee}-01-01", "end_date": f"{annee}-12-31",
            "daily": "temperature_2m_max,temperature_2m_min", "timezone": "auto"
        }
        
        data = requests.get(url, params=params).json()
        
        if "daily" in data:
            batch = []
            for i in range(len(data['daily']['time'])):
                dt = datetime.strptime(data['daily']['time'][i], "%Y-%m-%d")
                batch.append((ville, dt.year, dt.month, dt.day, 
                              data['daily']['temperature_2m_max'][i], 
                              data['daily']['temperature_2m_min'][i]))
            
            # "OR IGNORE" évite les erreurs si les données sont déjà là
            cursor.executemany('''
                INSERT OR IGNORE INTO archives_meteo (ville, annee, mois, jour, temp_max, temp_min)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', batch)
            
    conn.commit()
    conn.close()
    print("Base de données historique prête !")

if __name__ == "__main__":
    importer_annee_complete(2025)