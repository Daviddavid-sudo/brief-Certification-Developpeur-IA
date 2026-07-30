# LIVRABLE 2 : INGENIERIE DES COMPOSANTS D'INTELLIGENCE ARTIFICIELLE (BLOC 2)

## 1. Composant IA Générative : Assistant Text-to-SQL
Pour permettre aux utilisateurs non-techniques de poser des questions métiers en langage naturel (ex: *"Quel est le CA de la ville de Paris ?"*), un service d'extraction de requêtes SQL automatisé a été développé dans `services.py`.

### Architecture du Pipeline NLP
* **Framework :** LangChain (interconnexion via l'utilitaire `SQLDatabaseChain`).
* **Modèle de Langage (LLM) :** ChatGroq pour des temps de réponse ultra-rapides en inférence.
* **Validation des entrées :** Utilisation d'une liste blanche de mots-clés métiers (*population, département, CA, vente*) via la fonction `is_database_question` afin de rejeter les requêtes hors-sujet et optimiser la consommation de tokens.

### Sécurisation et Protection contre les Injections SQL
Afin de prémunir le système contre l'exécution de code malveillant généré par le LLM ou manipulé par l'utilisateur, une fonction de parsing stricte (`execute_ai_sql`) intercepte le code SQL avant soumission à la base de données :

```python
def execute_ai_sql(ai_response):
    ai_response = clean_sql_query(ai_response)
    match = re.search(r"SELECT\s+.*", ai_response, re.IGNORECASE | re.DOTALL)
    if not match: 
        return None
    
    sql = match.group(0).strip()
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
    
    # Blocage strict des requêtes de modification ou suppression
    if any(word in sql.upper() for word in forbidden):
        logger.warning("Dangerous SQL injection attempt blocked")
        return None