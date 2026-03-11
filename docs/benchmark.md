# Benchmark : Solutions d'IA pour l'Assistant de Données

## 1. Analyse du Besoin Fonctionnel
L'objectif du projet est de fournir une interface de "Chat-with-your-Data" permettant aux décideurs d'interroger les bases de données (INSEE, Ventes, Météo) en langage naturel sans compétences SQL.

**Critères d'évaluation :**
* **Précision SQL** : Capacité à générer des requêtes complexes (JOIN, GROUP BY).
* **Vitesse (Latence)** : Temps de réponse inférieur à 2 secondes pour une expérience fluide.
* **Sécurité** : Protection contre les injections SQL et isolation des données.
* **Intégration MLOps** : Compatibilité avec les outils de CI/CD et LangChain.

## 2. État de l'Art et Comparatif

| Solution | Modèle | Performance SQL | Latence | Coût |
| :--- | :--- | :--- | :--- | :--- |
| **OpenAI** | GPT-4o | Excellente | Moyenne | Élevé (Pay-per-token) |
| **Ollama** | Mistral/Llama 3 | Bonne | Variable (selon GPU local) | Gratuit |
| **Groq (LPUs)** | **Llama 3.3 70B** | **Excellente** | **Ultra-Rapide** | **Gratuit/Faible** |

## 3. Justification de la Sélection
Nous avons sélectionné l'architecture **Groq + Llama 3.3-70b-versatile** pour les raisons suivantes :

1. **Vitesse de traitement (Benchmark LPUs)** : Groq utilise des processeurs de langage (LPUs) qui permettent une génération de tokens 10x plus rapide que les architectures traditionnelles, garantissant un monitorage de performance optimal.
2. **Capacité du modèle** : Le modèle 70B est classé parmi les meilleurs pour la génération de code (SQL) et le raisonnement logique, minimisant les "hallucinations" de données.
3. **Interopérabilité** : L'écosystème LangChain facilite l'exposition du modèle via une API REST sécurisée (Django REST Framework).

## 4. Stratégie de Sécurité & Monitorage
Conformément aux exigences **OWASP**, la solution intègre :
* **Sanitisation** : Utilisation de Regex pour n'autoriser que les commandes `SELECT`.
* **Principe de Moindre Privilège** : Connexion à la base de données restreinte aux tables nécessaires via `SQLDatabase`.
* **Observabilité** : Mise en place d'un journal de métriques (`logs/ai_metrics.log`) pour suivre la latence et les erreurs en temps réel.

---
*Document rédigé dans le cadre de la veille technologique du projet.*