# LIVRABLE 1 : ARCHITECTURE LOGICIELLE ET FLUX DE DONNÉES (BLOC 1)

## 1. Introduction et Contexte Métier
Dans le cadre de l'optimisation des performances des points de vente, le pilotage par la donnée est devenu un enjeu stratégique majeur. Les décideurs font face à deux problématiques :
* L'incapacité d'interroger de manière agile les bases de données relationnelles sans compétences techniques en SQL.
* La difficulté d’anticiper les variations du Chiffre d’Affaires (CA) liées à des facteurs exogènes combinés, tels que la démographie locale et les aléas climatiques.

Ce projet implémente une solution web industrielle basée sur l'écosystème Django pour le backend métier et Streamlit pour le prototypage rapide (POC).

## 2. Modélisation Conceptuelle des Données (MCD)
La base de données repose sur trois tables principales modélisées dans Django (`models.py`), permettant le croisement multi-sources :

| Nom du Modèle Django | Champs Clés | Description & Source |
| :--- | :--- | :--- |
| **Population** | `dep` (Unique), `pop`, `region` | Données démographiques officielles de l'INSEE par département. |
| **MeteoArchive** | `dep`, `annee`, `mois`, `jour`, `temp_max`, `temp_min` | Historique météorologique journalier national (Clé composite unique). |
| **ActiviteCommerciale** | `code_dept`, `ville`, `ca_tot`, `annee`, `mois` | Suivi mensuel consolidé du chiffre d'affaires par entité. |

> 💡 *Note de l'étudiant : Lors de votre mise en page finale, intégrez ici le schéma situé dans `annexe/mcd.png`.*

## 3. Flux d'Ingestion et Automatisation
L'agrégation et le nettoyage des données brutes (fichiers CSV de l'INSEE, fichiers JSON des magasins et flux météo) s'effectuent via des scripts de commande Django natifs situés dans `dashboard/management/commands/` (ex: `import_insee.py`). Cela garantit l'intégrité référentielle avant l'exposition ou l'utilisation des données par les couches d'intelligence artificielle.