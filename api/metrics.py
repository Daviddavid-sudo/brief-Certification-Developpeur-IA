from prometheus_client import Counter, Histogram

AI_REQUEST_COUNT = Counter(
    "ai_requests_total",
    "Nombre total de requêtes IA"
)


AI_ERROR_COUNT = Counter(
    "ai_errors_total",
    "Nombre total d'erreurs IA"
)


AI_RESPONSE_TIME = Histogram(
    "ai_response_time_seconds",
    "Temps de réponse du service IA"
)