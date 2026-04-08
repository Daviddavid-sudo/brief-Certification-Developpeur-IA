import os
import re
import urllib.parse
import logging
from django.conf import settings
from django.db import connection
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain

logger = logging.getLogger('ai_monitoring')

def verify_and_clean_response(question, raw_data):
    """
    Vérifie la pertinence du résultat et le transforme en phrase humaine.
    Sert de filtre de sécurité pour éviter les sorties brutes ou incohérentes.
    """
    # 1. Gestion des résultats vides
    if raw_data is None or str(raw_data).strip() in ["None", "[]", "", "()"]:
        return "Je n'ai pas trouvé de données correspondant à cette recherche dans la base."

    # 2. Nettoyage strict des caractères Python (tuples, listes, guillemets)
    # Exemple: [('Nord', 2616909)] devient "Nord 2616909"
    clean_value = str(raw_data)
    for char in "[]()',":
        clean_value = clean_value.replace(char, "")
    clean_value = clean_value.strip()

    # 3. Formatage contextuel selon les mots-clés de la question
    q_lower = question.lower()
    
    if "pop" in q_lower or "habitant" in q_lower:
        return f"La population enregistrée est de : {clean_value} habitants."
    
    if "ca" in q_lower or "vente" in q_lower or "euro" in q_lower:
        return f"Le montant identifié est de : {clean_value} €."

    # 4. Fallback pour les autres types de questions (ex: listes de noms)
    return f"Voici le résultat de l'analyse : {clean_value}"


def ask_llm_about_db(question):
    """
    Service principal : SQL via IA -> Extraction brute -> Nettoyage et vérification Python.
    """
    db = None 
    try:
        # 1. Configuration de l'URI (Gère l'erreur d'hôte @127.0.0.1)
        db_conf = settings.DATABASES['default']
        if 'postgresql' in db_conf['ENGINE']:
            user = db_conf.get('USER') or 'postgres'
            pw = urllib.parse.quote_plus(db_conf.get('PASSWORD') or '')
            host = db_conf.get('HOST') or '127.0.0.1'
            port = db_conf.get('PORT') or '5432'
            name = db_conf.get('NAME') or 'certificate_dev'
            uri = f"postgresql+psycopg://{user}:{pw}@{host}:{port}/{name}"
        else:
            uri = f"sqlite:///{os.path.join(settings.BASE_DIR, db_conf['NAME'])}"

        # 2. Connexion à la DB (Tables spécifiques pour éviter les fuites)
        db = SQLDatabase.from_uri(
            uri, 
            include_tables=['dashboard_population', 'dashboard_activitecommerciale'],
            engine_args={"pool_pre_ping": True}
        )

        # 3. Setup LLM (Groq Llama 3)
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "Configuration Erreur : GROQ_API_KEY manquante."

        llm = ChatGroq(groq_api_key=api_key, model_name="llama-3.3-70b-versatile", temperature=0)

        # 4. Chaîne avec return_direct=True 
        # Crucial : L'IA renvoie la donnée brute, pas son log de pensée "SQLQuery/Result"
        db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True, return_direct=True)
        
        if hasattr(db_chain, 'allow_dangerous_requests'):
            db_chain.allow_dangerous_requests = True

        # 5. Exécution
        # On passe la question. Si c'est un "test", l'IA tentera un SQL ou échouera proprement.
        response = db_chain.invoke({"query": question})
        raw_data = response["result"] if isinstance(response, dict) else response

        # 6. Vérification finale et nettoyage
        return verify_and_clean_response(question, raw_data)

    except Exception as e:
        logger.error(f"AI Service Error: {str(e)}", exc_info=True)
        # Message poli en cas de question "test" qui n'aboutit pas à un SQL valide
        return "Désolé, je ne parviens pas à extraire cette information. Essayez de demander le chiffre d'affaires par ville ou la population d'un département."
    
    finally:
        # Libération systématique de la connexion
        if db and hasattr(db, '_engine'):
            db._engine.dispose()

def execute_ai_sql(ai_response):
    """ Utilitaire de secours pour exécuter du SQL brut si besoin """
    match = re.search(r"SELECT.*", ai_response, re.IGNORECASE | re.DOTALL)
    if not match: return None
    try:
        with connection.cursor() as cursor:
            cursor.execute(match.group(0).strip())
            return {"columns": [c[0] for c in cursor.description], "rows": cursor.fetchall()}
    except Exception:
        return None