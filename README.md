# brief-Certification-Developpeur-IA
# Certification Développeur IA — Plateforme d’Analyse Territoriale & Assistant IA SQL

## Présentation du projet

Ce projet est une plateforme web développée avec Django permettant :

* l’analyse de données territoriales françaises,
* l’exploitation de données démographiques INSEE,
* la consultation de données météo,
* l’exposition d’API REST,
* l’intégration d’un agent IA capable de générer des requêtes SQL automatiquement,
* le scraping de produits et de points de vente,
* la supervision et le monitoring des requêtes IA.

Le projet a été conçu dans une logique MLOps et Data Engineering avec :

* tests automatisés,
* monitoring,
* architecture modulaire,
* dockerisation,
* documentation API,
* intégration IA.

---

# Fonctionnalités principales

## Assistant IA SQL

Un agent IA connecté à la base de données permet de poser des questions en langage naturel.

Exemples :

* « Quel est le département avec la plus grande population ? »
* « Donne-moi la population du Nord »
* « Quel département possède le plus d’activités commerciales ? »

L’agent :

1. interprète la question,
2. génère une requête SQL,
3. interroge PostgreSQL/SQLite,
4. nettoie et reformule les résultats.

Technologies utilisées :

* LangChain
* Groq API
* Llama 3.3 70B
* SQLDatabaseChain

---

## API météo France

Une API REST permet d’obtenir des informations météo françaises.

Fonctionnalités :

* consultation météo,
* calendrier météo,
* intégration de données externes,
* endpoints REST documentés.

---

## Analyse démographique

Le projet exploite des données INSEE :

* population par département,
* visualisation géographique,
* cartes interactives,
* statistiques territoriales.

---

## Scraping & collecte de données

Le projet intègre plusieurs scripts de collecte :

* scraping de produits,
* récupération de points de vente,
* import automatisé de données,
* seed de données de démonstration.

Sources :

* INSEE
* données géographiques
* scraping e-commerce

---

## Monitoring & métriques IA

Le système surveille :

* le nombre de requêtes IA,
* les erreurs,
* les performances,
* les logs applicatifs.

Outils :

* Prometheus
* logs personnalisés
* métriques IA

---

# Architecture du projet

```bash
.
├── api/                    # API REST Django
├── dashboard/              # Application principale
├── data/                   # Jeux de données
├── docs/                   # Documentation technique
├── logs/                   # Logs et métriques
├── streamlit/              # POC Streamlit
├── tests/                  # Tests automatisés
├── docker-compose.yml
├── dockerfile
├── prometheus.yml
└── requirements.txt
```

---

# Structure détaillée

## dashboard/

Application principale contenant :

* modèles Django,
* vues,
* templates,
* services IA,
* logique métier,
* commandes de management.

### Services IA

Le fichier `services.py` contient :

* la connexion LLM,
* la génération SQL,
* la validation des requêtes,
* le nettoyage des réponses,
* les métriques IA.

---

## api/

Application REST exposant :

* endpoints météo,
* données analytiques,
* sérialisation JSON,
* documentation API.

---

## tests/

Le projet inclut plusieurs suites de tests :

### tests_ai_robustness.py

Validation de la robustesse de l’agent IA.

### tests_api.py

Tests des endpoints API.

### tests_metrics.py

Validation des métriques et logs.

### tests_mlops.py

Tests orientés monitoring et pipeline MLOps.

---

# Technologies utilisées

## Backend

* Python 3.12
* Django
* Django REST Framework

## Intelligence artificielle

* LangChain
* Groq API
* Llama 3.3 70B

## Base de données

* PostgreSQL
* SQLite

## Monitoring

* Prometheus
* Logging Python

## Data Engineering

* Pandas
* GeoJSON
* CSV
* Scraping

## Déploiement

* Docker
* Docker Compose

---

# Installation

## 1. Cloner le projet

```bash
git clone <repo_url>
cd brief-Certification-Developpeur-IA
```

---

## 2. Créer un environnement virtuel

```bash
python -m venv .venv
source .venv/bin/activate
```

---

## 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## 4. Variables d’environnement

Créer un fichier `.env` :

```env
GROQ_API_KEY=votre_cle_api
```

---

## 5. Migrations

```bash
python manage.py migrate
```

---

## 6. Charger les données

```bash
python manage.py seed_data
python manage.py import_insee
```

---

## 7. Lancer le serveur

```bash
python manage.py runserver
```

---

# Docker

## Lancer avec Docker Compose

```bash
docker-compose up --build
```

---

# Tests

Exécuter tous les tests :

```bash
python manage.py test
```

---

# Monitoring

Le projet inclut :

* logs IA,
* métriques Prometheus,
* supervision des requêtes.

Fichier principal :

```bash
prometheus.yml
```

---

# Documentation API

Documentation disponible dans :

```bash
docs/api_docs.yml
```

---

# Visualisations & annexes

Le dossier `annexe/` contient :

* schéma d’architecture,
* MCD,
* diagrammes techniques.

---

# Sécurité

Le système :

* limite les requêtes SQL dangereuses,
* filtre les entrées utilisateur,
* bloque les commandes SQL destructrices,
* nettoie les réponses LLM.

---

# Axes d’amélioration

* ajout d’authentification JWT,
* cache Redis,
* vectorisation RAG,
* dashboard temps réel,
* CI/CD avancé,
* Kubernetes,
* observabilité complète.

---

# Auteur

Projet réalisé dans le cadre de la certification Développeur IA.

Technologies IA, Data Engineering, Backend & MLOps appliquées à un cas d’analyse territoriale française.
