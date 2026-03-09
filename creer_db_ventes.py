import sqlite3

def ajouter_table_ventes():
    # On se connecte à la même base que pour la météo
    conn = sqlite3.connect('meteo_complete.db')
    cursor = conn.cursor()

    # Création de la table activite_commerciale
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activite_commerciale (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bv2022 TEXT,       -- Bassin de vie
            ville TEXT,        -- Ville (doit correspondre au nom dans la table météo)
            ca_tot REAL,       -- Chiffre d'affaires
            mois INTEGER,
            annee INTEGER,
            UNIQUE(ville, mois, annee) -- Sécurité doublons
        )
    ''')

    conn.commit()
    conn.close()
    print("Table 'activite_commerciale' ajoutée à la base météo !")

if __name__ == "__main__":
    ajouter_table_ventes()