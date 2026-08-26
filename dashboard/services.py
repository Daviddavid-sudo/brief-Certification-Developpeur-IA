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

from prometheus_client import Counter


logger = logging.getLogger("ai_monitoring")


# =========================================================
# METRICS
# =========================================================

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
    "ventes",
    "revenu",
    "entreprise",
]


def is_database_question(question: str) -> bool: """ Vérifie si la question concerne les données métier et bloque les commandes SQL dangereuses. """ if not question: return False q = question.lower().strip() # Questions invalides if q in INVALID_INPUTS: return False # Bloquer les commandes SQL dangereuses forbidden_sql = [ "drop", "delete", "update", "insert", "alter", "truncate", "create", "grant", "revoke", ] for command in forbidden_sql: if re.search(rf"\b{command}\b", q): return False # Vérifier les mots-clés métier return any( keyword in q for keyword in DB_KEYWORDS )


# =========================================================
# SQL CLEANER
# =========================================================

def clean_sql_query(query: str) -> str:
    """
    Nettoie une requête SQL générée par le LLM.
    """

    if not query:
        return ""

    query = query.strip()

    query = re.sub(
        r"^```sql\s*",
        "",
        query,
        flags=re.IGNORECASE
    )

    query = re.sub(
        r"^```\s*",
        "",
        query
    )

    query = re.sub(
        r"\s*```$",
        "",
        query
    )

    return query.strip()


# =========================================================
# RESULT NORMALIZATION
# =========================================================

def normalize_result(raw_data):
    """
    Transforme le résultat SQL en texte lisible.
    """

    if raw_data is None:
        return None

    if isinstance(raw_data, str):
        raw_data = raw_data.strip()

        if raw_data in ("", "[]", "()", "None"):
            return None

    try:

        parsed = ast.literal_eval(str(raw_data))

        if isinstance(parsed, list):

            if len(parsed) == 0:
                return None

            first = parsed[0]

            if isinstance(first, tuple):
                return " - ".join(
                    str(value) for value in first
                )

            return str(first)

        if isinstance(parsed, tuple):

            return " - ".join(
                str(value) for value in parsed
            )

        return str(parsed)

    except Exception:

        return str(raw_data).strip()


# =========================================================
# RESPONSE CLEANER
# =========================================================

def verify_and_clean_response(question, raw_data):
    """
    Transforme le résultat SQL en réponse compréhensible.
    """

    if raw_data is None:
        return (
            "Je n'ai trouvé aucune donnée "
            "correspondant à votre demande."
        )

    clean_value = normalize_result(raw_data)

    if not clean_value:
        return (
            "Je n'ai trouvé aucune donnée "
            "correspondant à votre demande."
        )

    q_lower = question.lower()

    # -----------------------------------------------------
    # Population
    # -----------------------------------------------------

    if (
        "population" in q_lower
        or "habitant" in q_lower
    ):

        if (
            "département" in q_lower
            or "departement" in q_lower
        ):

            return (
                "Le département ayant la plus grande "
                f"population est : {clean_value}."
            )

        if "région" in q_lower or "region" in q_lower:

            return (
                "La région correspondant au résultat "
                f"est : {clean_value}."
            )

        return (
            f"La population enregistrée est : "
            f"{clean_value} habitants."
        )

    # -----------------------------------------------------
    # Chiffre d'affaires / ventes
    # -----------------------------------------------------

    if (
        "ca" in q_lower
        or "chiffre d'affaires" in q_lower
        or "chiffre" in q_lower
        or "vente" in q_lower
        or "revenu" in q_lower
    ):

        return (
            f"Le montant identifié est : "
            f"{clean_value} €."
        )

    # -----------------------------------------------------
    # Réponse générique
    # -----------------------------------------------------

    return (
        f"Voici le résultat trouvé : {clean_value}"
    )


# =========================================================
# DATABASE URI
# =========================================================

def build_database_uri():
    """
    Construit automatiquement l'URI SQLAlchemy
    à partir de la configuration Django.
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
            f"{user}:{password}@"
            f"{host}:{port}/{db_name}"
        )

    # SQLite
    return (
        "sqlite:///"
        f"{os.path.join(settings.BASE_DIR, db_conf['NAME'])}"
    )


# =========================================================
# CUSTOM SQL PROMPT
# =========================================================

SQL_PROMPT = PromptTemplate(
    input_variables=[
        "input",
        "table_info",
        "dialect",
    ],
    template="""
You are a PostgreSQL expert working with a French business database.

Your task is to convert the user's question into ONE valid PostgreSQL SQL query.

IMPORTANT RULES:

1. Return ONLY the SQL query.
2. Do NOT use Markdown.
3. Do NOT use ```sql.
4. Do NOT explain the query.
5. Do NOT add comments.
6. ONLY generate SELECT queries.
7. NEVER generate INSERT, UPDATE, DELETE, DROP, ALTER or TRUNCATE.
8. Use ONLY the tables provided in the database schema.
9. Use the exact column names from the database.
10. If the user asks for the largest, highest, biggest or maximum value, use ORDER BY DESC and LIMIT 1.
11. If the user asks for the smallest, lowest or minimum value, use ORDER BY ASC and LIMIT 1.

DATABASE INFORMATION

Table dashboard_population:

- departement = name of the French department
- dep = department code
- pop = population
- region = name of the region
- reg = region code
- date_import = import date

Table dashboard_activitecommerciale:

Use ONLY the columns actually present in the schema below.

IMPORTANT POPULATION EXAMPLE:

Question:
Quel est le département avec la plus grande population ?

SQL:
SELECT departement, pop
FROM dashboard_population
ORDER BY pop DESC
LIMIT 1;

IMPORTANT SALES EXAMPLE:

Question:
Quel département possède le chiffre d'affaires le plus élevé ?

SQL:
SELECT dep, ca_tot
FROM dashboard_activitecommerciale
ORDER BY ca_tot DESC
LIMIT 1;

DATABASE SCHEMA:

{table_info}

USER QUESTION:

{input}

Return ONLY the SQL query.
"""
)


# =========================================================
# MAIN AI SERVICE
# =========================================================

def ask_llm_about_db(question):
    """
    Pipeline :

    Question utilisateur
            ↓
    Validation
            ↓
    LLM
            ↓
    Génération SQL
            ↓
    PostgreSQL
            ↓
    Résultat
            ↓
    Réponse utilisateur
    """

    AI_REQUEST_COUNT.inc()

    db = None

    try:

        # =================================================
        # 1. Validation de la question
        # =================================================

        if not is_database_question(question):

            return (
                "Je peux répondre uniquement aux questions "
                "liées à la population et aux activités "
                "commerciales."
            )

        # =================================================
        # 2. Connexion PostgreSQL
        # =================================================

        uri = build_database_uri()

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

        # =================================================
        # 3. Vérification API Groq
        # =================================================

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:

            logger.error("GROQ_API_KEY manquante")

            return "Erreur de configuration du service IA."

        # =================================================
        # 4. Initialisation du modèle
        # =================================================

        llm = ChatGroq(
            groq_api_key=api_key,
            model_name="openai/gpt-oss-120b",
            temperature=0,
        )

        # =================================================
        # 5. Création de la chaîne SQL
        # =================================================

        db_chain = SQLDatabaseChain.from_llm(
            llm=llm,
            db=db,
            prompt=SQL_PROMPT,

            # TEMPORAIRE :
            # permet de voir le SQL généré
            verbose=True,

            return_direct=True,

            use_query_checker=False,
        )

        # =================================================
        # 6. Exécution
        # =================================================

        response = db_chain.invoke({
            "query": question
        })

        # =================================================
        # 7. Logs de diagnostic
        # =================================================

        print("\n==============================")
        print("QUESTION UTILISATEUR")
        print("==============================")
        print(question)

        print("\n==============================")
        print("REPONSE LANGCHAIN")
        print("==============================")
        print(response)

        print("==============================\n")

        # =================================================
        # 8. Extraction du résultat
        # =================================================

        if isinstance(response, dict):

            raw_data = response.get("result")

        else:

            raw_data = response

        # =================================================
        # 9. Transformation en réponse naturelle
        # =================================================

        return verify_and_clean_response(
            question,
            raw_data
        )

    except Exception as e:

        logger.error(
            f"AI Service Error: {str(e)}",
            exc_info=True
        )

        print("\n==============================")
        print("ERREUR SERVICE IA")
        print("==============================")
        print(str(e))
        print("==============================\n")

        return (
            "Désolé, une erreur est survenue "
            "lors de l'analyse des données."
        )

    finally:

        # =================================================
        # 10. Fermeture connexion SQLAlchemy
        # =================================================

        try:

            if db and hasattr(db, "_engine"):

                db._engine.dispose()

        except Exception:

            pass


# =========================================================
# SECURE RAW SQL EXECUTOR
# =========================================================

def execute_ai_sql(ai_response):
    """
    Exécute uniquement des requêtes SELECT.
    """

    if not ai_response:
        return None

    ai_response = clean_sql_query(
        ai_response
    )

    # -----------------------------------------------------
    # Recherche de SELECT
    # -----------------------------------------------------

    match = re.search(
        r"SELECT\s+.*",
        ai_response,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return None

    sql = match.group(0).strip()

    # -----------------------------------------------------
    # Sécurité
    # -----------------------------------------------------

    forbidden = [
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "GRANT",
        "REVOKE",
    ]

    upper_sql = sql.upper()

    if any(
        re.search(
            rf"\b{word}\b",
            upper_sql
        )
        for word in forbidden
    ):

        logger.warning(
            "Tentative d'exécution SQL dangereuse bloquée."
        )

        return None

    # -----------------------------------------------------
    # Exécution
    # -----------------------------------------------------

    try:

        with connection.cursor() as cursor:

            cursor.execute(sql)

            return {
                "columns": [
                    column[0]
                    for column in cursor.description
                ],
                "rows": cursor.fetchall(),
            }

    except Exception as e:

        logger.error(
            f"Raw SQL execution failed: {str(e)}",
            exc_info=True,
        )

        return None