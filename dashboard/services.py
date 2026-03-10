import os
from django.conf import settings
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain

def ask_llm_about_db(question):
    """
    Connects to the Django database and uses an LLM to generate and run SQL.
    """
    
    # 1. DATABASE CONNECTION
    # We fetch the DB path from settings.py and ensure it is an absolute path
    db_name = settings.DATABASES['default']['NAME']
    
    # If the path is not already absolute (common in SQLite), we join it with BASE_DIR
    if not os.path.isabs(db_name):
        db_path = os.path.join(settings.BASE_DIR, db_name)
    else:
        db_path = db_name

    # Create the SQLAlchemy engine for LangChain
    # Note: For Postgres/MySQL, this string would change to 'postgresql://user:pass@host/db'
    engine_url = f"sqlite:///{db_path}"
    db = SQLDatabase.from_uri(engine_url)

    # 2. LLM INITIALIZATION
    # It is best practice to use environment variables for keys
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        return "Error: GROQ_API_KEY not found. Please run 'export GROQ_API_KEY=your_key'"

    # Change the model_name here
    llm = ChatGroq(
        groq_api_key=api_key,
        model_name="llama-3.3-70b-versatile", # Updated model name
        temperature=0
    )

    # 3. SQL CHAIN CREATION
    # allow_dangerous_requests is required in current versions to enable SQL execution
    # Remove the allow_dangerous_requests line
    db_chain = SQLDatabaseChain.from_llm(
        llm, 
        db, 
        verbose=True
)

    # 4. EXECUTION
    try:
        # .invoke() is the modern replacement for .run()
        response = db_chain.invoke({"query": question})
        return response["result"]
    except Exception as e:
        return f"Erreur lors de la requête : {str(e)}"