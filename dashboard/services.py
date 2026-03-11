import os
import re
import time
import logging
from django.conf import settings
from django.db import connection
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from prometheus_client import Histogram, Counter

# 1. Metrics setup
AI_REQUEST_LATENCY = Histogram(
    "ai_request_latency_seconds",
    "Latency of AI database queries"
)

AI_REQUEST_COUNT = Counter(
    "ai_request_total",
    "Total number of AI assistant queries"
)

AI_ERRORS = Counter(
    "ai_errors_total",
    "Total number of AI assistant errors"
)

logger = logging.getLogger('ai_monitoring')

def ask_llm_about_db(question):
    """
    Main service to handle AI queries. 
    Increments metrics and manages DB connections safely.
    """
    start_time = time.time()
    AI_REQUEST_COUNT.inc()
    
    db = None  # Initialized for the finally block

    try:
        # 2. Dynamic DB Configuration
        db_conf = settings.DATABASES['default']
        
        if 'postgresql' in db_conf['ENGINE']:
            # Construct PostgreSQL URI (Compatible with psycopg-binary==3.3.3)
            uri = f"postgresql+psycopg://{db_conf['USER']}:{db_conf['PASSWORD']}@{db_conf['HOST']}:{db_conf['PORT']}/{db_conf['NAME']}"
        else:
            # Fallback for local SQLite
            db_name = db_conf['NAME']
            db_path = os.path.join(settings.BASE_DIR, db_name) if not os.path.isabs(db_name) else db_name
            uri = f"sqlite:///{db_path}"

        # 3. Connect to Database
        db = SQLDatabase.from_uri(
            uri,
            include_tables=['dashboard_population', 'dashboard_activitecommerciale']
        )

        # 4. API Key Safety Check
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            AI_ERRORS.inc()
            return "Error: GROQ_API_KEY non configurée."

        # 5. LLM and Chain Logic
        llm = ChatGroq(
            groq_api_key=api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0
        )

        db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True, return_direct=False)
        
        if hasattr(db_chain, 'allow_dangerous_requests'):
            db_chain.allow_dangerous_requests = True

        full_prompt = (
            "Tu es un analyste expert. Crée la requête SQL, exécute-la, "
            "et donne la réponse finale en français.\n"
            f"Question: {question}"
        )

        # Execute
        if hasattr(db_chain, 'invoke'):
            output = db_chain.invoke({"query": full_prompt})
            final_text = output["result"] if isinstance(output, dict) else output
        else:
            final_text = db_chain.run(full_prompt)

        # 6. Record Latency
        latency = time.time() - start_time
        AI_REQUEST_LATENCY.observe(latency)

        return final_text

    except Exception as e:
        AI_ERRORS.inc()
        logger.error(f"AI Service Error: {str(e)}")
        return f"Erreur d'analyse : {str(e)}"
    
    finally:
        # 7. CRITICAL: Close DB connections to release locks for CI/CD
        if db and hasattr(db, '_engine'):
            db._engine.dispose()

def execute_ai_sql(ai_response):
    """
    OWASP Security Check: Extract and execute SELECT queries only.
    """
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