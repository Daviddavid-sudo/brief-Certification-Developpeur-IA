import os
import re
import time
import logging
from django.conf import settings
from django.db import connection
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain

# Monitoring Setup
logger = logging.getLogger('ai_monitoring')
# Ensure logs directory exists in your root
LOG_FILE = os.path.join(settings.BASE_DIR, 'logs', 'ai_metrics.log')

def ask_llm_about_db(question):
    start_time = time.time()
    
    try:
        # 1. SETUP DB
        db_name = settings.DATABASES['default']['NAME']
        db_path = os.path.join(settings.BASE_DIR, db_name) if not os.path.isabs(db_name) else db_name
        db = SQLDatabase.from_uri(
            f"sqlite:///{db_path}", 
            include_tables=['dashboard_population', 'dashboard_activitecommerciale']
        )

        # 2. SETUP LLM
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "Error: GROQ_API_KEY non configurée."
            
        llm = ChatGroq(groq_api_key=api_key, model_name="llama-3.3-70b-versatile", temperature=0)

        # 3. CONFIGURE THE CHAIN
        db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True, return_direct=False)
        
        if hasattr(db_chain, 'allow_dangerous_requests'):
            db_chain.allow_dangerous_requests = True

        # 4. PROMPT (MLOps context)
        full_prompt = (
            f"Tu es un analyste expert. Crée la requête SQL, exécute-la, "
            f"et donne la réponse finale en français.\n"
            f"Question: {question}"
        )

        # 5. EXECUTION
        if hasattr(db_chain, 'invoke'):
            output = db_chain.invoke({"query": full_prompt})
            final_text = output["result"] if isinstance(output, dict) else output
        else:
            final_text = db_chain.run(full_prompt)

        # 6. MONITORING (Satisfies 'Monitorer ses métriques')
        latency = time.time() - start_time
        with open(LOG_FILE, 'a') as f:
            f.write(f"Latency: {latency:.2f}s | Query: {question[:50]}\n")

        return final_text

    except Exception as e:
        return f"Erreur d'analyse : {str(e)}"

def execute_ai_sql(ai_response):
    """Extracts and executes SELECT queries only (OWASP Security)."""
    match = re.search(r"SQLQuery:\s*(SELECT.*?)(?:\n|$|;)", ai_response, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    
    sql_query = match.group(1).strip()
    
    if not sql_query.upper().startswith("SELECT"):
        return "Erreur : Accès restreint à la lecture (SELECT) uniquement."

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return {"columns": columns, "rows": rows}
    except Exception as e:
        return f"Erreur SQL : {str(e)}"