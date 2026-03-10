import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import os

# --- CONFIG & ASSETS ---
st.set_page_config(page_title="France Data Dashboard", layout="wide")

# Mocking the path - Ensure your departments.geojson is in a /data folder
PATH_GEOJSON = os.path.join('data', 'departements.geojson')

@st.cache_data
def load_geo_data():
    if os.path.exists(PATH_GEOJSON):
        return gpd.read_file(PATH_GEOJSON)
    else:
        st.error(f"File not found: {PATH_GEOJSON}")
        return None

# --- MOCK DATA GENERATORS (Replacing Django Models) ---
def get_mock_sales_data():
    return pd.DataFrame({
        'code_dept': ['75', '59', '13', '69', '33', '44'],
        'ca_tot': [150000, 85000, 92000, 110000, 75000, 60000]
    })

def get_mock_meteo_data(date_obj):
    # Simulating data for specific cities
    return pd.DataFrame({
        'ville': ["Paris", "Lille", "Marseille", "Lyon"],
        'temp_min': [12, 8, 18, 14],
        'code_dept': ["75", "59", "13", "69"]
    })

# --- NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Aller à", ["Carte des Ventes", "Météo & Températures", "Démographie"])

france = load_geo_data()

if france is None:
    st.warning("Veuillez ajouter le fichier 'departements.geojson' dans le dossier /data pour voir les cartes.")
    st.stop()

# --- PAGE 1: SALES MAP ---
if page == "Carte des Ventes":
    st.header("📊 Répartition du Chiffre d'Affaires")
    
    df_ventes = get_mock_sales_data()
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    df_regroupe = df_ventes.groupby('code_dept')['ca_tot'].sum().reset_index()
    merged = france.merge(df_regroupe, left_on='code', right_on='code_dept', how='left')
    
    merged.plot(column='ca_tot', ax=ax, legend=True, cmap='OrRd', 
                missing_kwds={'color': 'lightgrey'}, 
                legend_kwds={'label': "Chiffre d'Affaires (€)"})
    
    ax.set_axis_off()
    st.pyplot(fig)
    st.table(df_ventes) # Display raw data below

# --- PAGE 2: WEATHER ---
elif page == "Météo & Températures":
    st.header("🌡️ Consultation Météo Archive")
    
    date_choisie = st.date_input("Choisir une date")
    
    if date_choisie:
        df_meteo = get_mock_meteo_data(date_choisie)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig, ax = plt.subplots(1, 1, figsize=(8, 8))
            merged = france.merge(df_meteo, left_on='code', right_on='code_dept', how='left')
            
            merged.plot(column='temp_min', ax=ax, legend=True, cmap='coolwarm',
                        missing_kwds={'color': '#f0f0f0'},
                        legend_kwds={'label': "Température Minimale (°C)"})
            ax.set_axis_off()
            ax.set_title(f"Températures le {date_choisie}")
            st.pyplot(fig)
            
        with col2:
            st.write("Détails par ville")
            st.dataframe(df_meteo[['ville', 'temp_min']])

# --- PAGE 3: POPULATION ---
elif page == "Démographie":
    st.header("👥 Répartition de la Population Jeune")
    
    data_pop = {'75': 18.5, '59': 24.2, '13': 22.1, '69': 21.8, '93': 28.5, '33': 20.4}
    df_pop = pd.DataFrame(list(data_pop.items()), columns=['code_dept', 'taux_jeunes'])
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    merged = france.merge(df_pop, left_on='code', right_on='code_dept', how='left')
    
    merged.plot(column='taux_jeunes', ax=ax, legend=True, cmap='YlGn', 
                missing_kwds={'color': '#f5f5f5'}, 
                legend_kwds={'label': "% de population < 18 ans"})
    
    ax.set_axis_off()
    st.pyplot(fig)