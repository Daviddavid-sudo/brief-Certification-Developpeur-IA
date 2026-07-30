### 📄 Fichier 3 : `LIVRABLE_3_DEPLOIEMENT_MLOPS.md`
*(Correspond au **Bloc 3** du référentiel RNCP37827)*

```markdown
# LIVRABLE 3 : DEPLOIEMENT, INTERFACE ET MONITORING (BLOC 3)

## 1. Interface Utilisateur (Prototypage Streamlit)
L'application `streamlit/poc.py` sert de démonstrateur technologique interactif. Elle se connecte de manière autonome à la base de données SQLite du projet grâce à un moteur SQLAlchemy et propose plusieurs onglets applicatifs :
1. **Carte des Ventes :** Rendu cartographique national exploitant GeoPandas et le fichier `departements.geojson`.
2. **Analyse Météo :** Corrélation visuelle et filtrage par date des températures historiques.
3. **Console Assistant :** Zone d'interaction directe en langage naturel connectée au service LLM.

## 2. Stratégie de Tests et Robustesse de l'IA
Pour valider la stabilité de la solution logicielle avant son déploiement, le dossier `tests/` intègre une automatisation complète :
* `tests_ai_robustness.py` : Simule des attaques par injection de prompts ou des saisies utilisateur aberrantes pour valider l'étanchéité des filtres de sécurité.
* `tests_api.py` : Contrôle la disponibilité et la performance des codes de réponse HTTP des endpoints REST Django.

## 3. Supervision de Production (MLOps)
Conformément aux exigences de mise en production et de maintien en condition opérationnelle (MCO), l'application intègre une couche d'observabilité complète :

| Composant MLOps | Fichier de Configuration | Rôle Fonctionnel |
| :--- | :--- | :--- |
| **Prometheus Counter** | `services.py` (`AI_REQUEST_COUNT`) | Mesure en temps réel du volume de requêtes IA traitées et détection des anomalies de parsing. |
| **Prometheus Server** | `prometheus.yml` | Scrape à intervalles réguliers les métriques de performance exposées. |
| **Docker Compose** | `docker-compose.yml` | Orchestration et isolation globale des conteneurs (Base de données, Application Django, Streamlit, Prometheus). |