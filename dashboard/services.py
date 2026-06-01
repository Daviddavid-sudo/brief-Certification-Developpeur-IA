import os
import re
import ast
import urllib.parse
import logging

from django.conf import settings
from django.db import connection

from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_core.prompts import PromptTemplate

# Imported Prometheus Counter to track metrics properly
from prometheus_client import Counter

logger = logging.getLogger("ai_monitoring")

# =========================================================
# METRICS
# =========================================================

# Redefined as a Prometheus Counter object to support ._value.get() in tests
AI_REQUEST_COUNT = Counter(
    "ai_request_count_total", 
    "Total number of AI requests processed"
)


# =========================================================
# INPUT VALIDATION
# =========================================================

INVALID_INPUTS = {
    "test",
    "hello",
    "hi",
    "hey",
    "salut",
    "ok",
    "?",
    "??",
    "...",
}


DB_KEYWORDS = [
    "population",
    "habitant",
    "habitants",
    "ville",
    "département",
    "departement",
    "commerce",
    "commercial",
    "activité",
    "activite",
    "ca",
    "chiffre",
    "vente",
    "revenu",
    "entreprise",
]


def is_database_question(question: str) -> bool:
    """
    Vérifie si la question semble liée aux données métier.
    """

    if not question:
        return False

    q = question.lower().strip()

    if q in INVALID_INPUTS:
        return False

    return any(keyword in q for keyword in DB_KEYWORDS)


# =========================================================
# SQL CLEANER
# =========================================================

def clean_sql_query(query: str) -> str:
    """
    Supprime les blocs markdown ```sql
    """

    if not query:
        return query

    query = query.strip()

    # Remove ```sql
    query = re.sub(
        r"^```sql",
        "",
        query,
        flags=re.IGNORECASE
    )

    # Remove ```
    query = re.sub(
        r"```$",
        "",
        query
    )

    return query.strip()


# =========================================================
# RESULT NORMALIZATION
# =========================================================

def normalize_result(raw_data):
    """
    Transforme tuples/listes SQL en texte lisible.
    """

    if raw_data is None:
        return None

    try:

        parsed = ast.literal_eval(str(raw_data))

        # [('Nord', 2616909)]
        if isinstance(parsed, list) and len(parsed) > 0:

            first = parsed[0]

            if isinstance(first, tuple):

                return " - ".join(
                    str(x) for x in first
                )

            return str(first)

        # ('Nord', 2616909)
        if isinstance(parsed, tuple):

            return " - ".join(
                str(x) for x in parsed
            )

        return str(parsed)

    except Exception:

        return str(raw_data).strip()


# =========================================================
# RESPONSE CLEANER
# =========================================================

def verify_and_clean_response(question, raw_data):
    """
    Transforme les résultats SQL en phrase naturelle.
    """

    if raw_data is None or str(raw_data).strip() in [
        "",
        "[]",
        "()",
        "None",
    ]:
        return (
            "Je n'ai trouvé aucune donnée "
            "correspondant à votre demande."
        )

    clean_value = normalize_result(raw_data)

    q_lower = question.lower()

    # Population
    if (
        "population" in q_lower
        or "habitant" in q_lower
    ):
        return (
            f"La population enregistrée est : "
            f"{clean_value} habitants."
        )

    # Chiffre d'affaires
    if (
        "ca" in q_lower
        or "chiffre" in q_lower
        or "vente" in q_lower
        or "revenu" in q_lower
        or "euro" in q_lower
    ):
        return (
            f"Le montant identifié est : "
            f"{clean_value} €."
        )

    return f"Voici le résultat trouvé : {clean_value}"


# =========================================================
# DATABASE URI
# =========================================================

def build_database_uri():
    """
    Construit automatiquement l'URI SQLAlchemy.
    """

    db_conf = settings.DATABASES["default"]

    # PostgreSQL
    if "postgresql" in db_conf["ENGINE"]:

        user = db_conf.get("USER") or "postgres"

        password = urllib.parse.quote_plus(
            db_conf.get("PASSWORD") or ""
        )

        host = db_conf.get("HOST") or "127.0.0.1"

        port = db_conf.get("PORT") or "5432"

        db_name = db_conf.get("NAME") or "postgres"

        return (
            f"postgresql+psycopg://"
            f"{user}:{password}@{host}:{port}/{db_name}"
        )

    # SQLite
    return (
        f"sqlite:///"
        f"{os.path.join(settings.BASE_DIR, db_conf['NAME'])}"
    )


# =========================================================
# CUSTOM PROMPT
# =========================================================

SQL_PROMPT = PromptTemplate(
    input_variables=[
        "input",
        "table_info",
        "dialect",
    ],
    template="""
You are a PostgreSQL expert.

Generate ONLY raw SQL.

IMPORTANT:
- DO NOT use markdown
- DO NOT use ```sql
- DO NOT explain anything
- DO NOT add comments
- ONLY return executable SQL

Question:
{input}

Available tables:
{table_info}
"""
)


# =========================================================
# MAIN AI SERVICE
# =========================================================

def ask_llm_about_db(question):
    """
    Pipeline principal :
    Question -> SQL -> DB -> Réponse propre
    """

    # Incremented the Prometheus counter object
    AI_REQUEST_COUNT.inc()

    db = None

    try:

        # ---------------------------------------------
        # 1. Validate question
        # ---------------------------------------------

        if not is_database_question(question):

            return (
                "Je peux répondre uniquement "
                "aux questions liées à la population "
                "et aux activités commerciales."
            )

        # ---------------------------------------------
        # 2. Database URI
        # ---------------------------------------------

        uri = build_database_uri()

        # ---------------------------------------------
        # 3. SQL Database
        # ---------------------------------------------

        db = SQLDatabase.from_uri(
            uri,
            include_tables=[
                "dashboard_population",
                "dashboard_activitecommerciale",
            ],
            engine_args={
                "pool_pre_ping": True,
            },
        )

        # ---------------------------------------------
        # 4. API KEY
        # ---------------------------------------------

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:

            logger.error("Missing GROQ_API_KEY")

            return "Erreur configuration IA."

        # ---------------------------------------------
        # 5. LLM
        # ---------------------------------------------

        llm = ChatGroq(
            groq_api_key=api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0,
        )

        # ---------------------------------------------
        # 6. SQL CHAIN
        # ---------------------------------------------

        db_chain = SQLDatabaseChain.from_llm(
            llm=llm,
            db=db,

            # Custom prompt
            prompt=SQL_PROMPT,

            # Disable verbose logs
            verbose=False,

            # Return only SQL result
            return_direct=True,

            # IMPORTANT:
            # Query checker disabled because
            # it often injects markdown
            use_query_checker=False,
        )

        # ---------------------------------------------
        # 7. Execute
        # ---------------------------------------------

        response = db_chain.invoke({
            "query": question
        })

        raw_data = (
            response.get("result")
            if isinstance(response, dict)
            else response
        )

        # ---------------------------------------------
        # 8. Clean final response
        # ---------------------------------------------

        return verify_and_clean_response(
            question,
            raw_data
        )

    except Exception as e:

        logger.error(
            f"AI Service Error: {str(e)}",
            exc_info=True
        )

        return (
            "Désolé, une erreur est survenue "
            "lors de l'analyse des données."
        )

    finally:

        # ---------------------------------------------
        # 9. Close DB engine
        # ---------------------------------------------

        try:

            if db and hasattr(db, "_engine"):
                db._engine.dispose()

        except Exception:
            pass


# =========================================================
# OPTIONAL RAW SQL EXECUTOR
# =========================================================

def execute_ai_sql(ai_response):
    """
    Utilitaire de secours :
    exécute uniquement des SELECT.
    """

    if not ai_response:
        return None

    ai_response = clean_sql_query(ai_response)

    match = re.search(
        r"SELECT\s+.*",
        ai_response,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return None

    sql = match.group(0).strip()

    # SECURITY BLOCK
    forbidden = [
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "ALTER",
        "TRUNCATE",
    ]

    upper_sql = sql.upper()

    if any(word in upper_sql for word in forbidden):

        logger.warning(
            "Dangerous SQL blocked"
        )

        return None

    try:

        with connection.cursor() as cursor:

            cursor.execute(sql)

            return {
                "columns": [
                    c[0]
                    for c in cursor.description
                ],
                "rows": cursor.fetchall(),
            }

    except Exception as e:

        logger.error(
            f"Raw SQL execution failed: {str(e)}",
            exc_info=True,
        )

        return None
