import os

from langchain_groq import ChatGroq


def create_ai_service():
    """
    Ancienne configuration du service IA.
    """

    api_key = os.getenv("GROQ_API_KEY")

    llm = ChatGroq(
        groq_api_key=api_key,
        model_name="llama-3.3-70b-versatile",
        temperature=0,
    )

    return llm

import os

from langchain_groq import ChatGroq


def create_ai_service():
    """
    Configuration corrigée du service IA.
    """

    api_key = os.getenv("GROQ_API_KEY")

    llm = ChatGroq(
        groq_api_key=api_key,
        model_name="openai/gpt-oss-120b",
        temperature=0,
    )

    return llm

