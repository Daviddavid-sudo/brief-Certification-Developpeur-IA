import os
from django.conf import settings
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain

def ask_llm_about_db(question):
    # 1. SETUP DB
    db_name = settings.DATABASES['default']['NAME']
    db_path = os.path.join(settings.BASE_DIR, db_name) if not os.path.isabs(db_name) else db_name
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}", include_tables=['dashboard_population', 'dashboard_activitecommerciale'])

    # 2. SETUP LLM
    api_key = os.getenv("GROQ_API_KEY")
    llm = ChatGroq(groq_api_key=api_key, model_name="llama-3.3-70b-versatile", temperature=0)

    # 3. CONFIGURE THE CHAIN
    # We explicitly tell it NOT to return just the SQL, but the final text.
    db_chain = SQLDatabaseChain.from_llm(
        llm, 
        db, 
        verbose=True, 
        return_direct=False  # This is key: False means "Give me the final sentence"
    )
    
    # Handle the safety flag if exists
    if hasattr(db_chain, 'allow_dangerous_requests'):
        db_chain.allow_dangerous_requests = True

    # 4. THE PROMPT (The "Magic" instructions)
    # We force the LLM to follow the chain: Question -> SQL -> Result -> Final Answer
    full_prompt = (
        f"Instructions: Crée la requête SQL, exécute-la sur la base, "
        f"puis utilise le résultat pour rédiger une réponse amicale en français.\n"
        f"Question: {question}"
    )

    # 5. EXECUTION
    try:
        # We use .invoke() or .run() based on your version
        if hasattr(db_chain, 'invoke'):
            output = db_chain.invoke({"query": full_prompt})
            # result might be a dict or a string depending on version
            return output["result"] if isinstance(output, dict) else output
        else:
            return db_chain.run(full_prompt)
    except Exception as e:
        return f"Erreur d'analyse : {str(e)}"

import re
from django.db import connection

def execute_ai_sql(ai_response):
    """
    Extracts the SQL query from the AI text and executes it if it's a SELECT.
    """
    # Look for the SQLQuery: part of the response
    match = re.search(r"SQLQuery:\s*(SELECT.*?)(?:\n|$|;)", ai_response, re.IGNORECASE | re.DOTALL)
    
    if not match:
        return None  # No SQL found
    
    sql_query = match.group(1).strip()
    
    # Safety Check: ONLY allow SELECT
    if not sql_query.upper().startswith("SELECT"):
        return "Erreur : Seules les requêtes de lecture sont autorisées."

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            # Get column names (headers)
            columns = [col[0] for col in cursor.description]
            # Get the actual data
            rows = cursor.fetchall()
            
            return {"columns": columns, "rows": rows}
    except Exception as e:
        return f"Erreur SQL : {str(e)}"