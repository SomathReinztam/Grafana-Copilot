"""Fábrica de LLM (Gemini) y helper para el contenido lista-de-dicts de Gemini."""
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from app.settings import settings


def make_llm(temperature: float = 0.2, model: str | None = None) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=model or settings.gemini_model,
        temperature=temperature,
        google_api_key=settings.google_api_key,
    )


def extract_text(msg: Any) -> str:
    """Gemini vía LangChain devuelve el contenido como str o como lista de dicts
    (con texto y a veces una 'firma'/signature). Extrae solo el texto de forma robusta.
    """
    content = getattr(msg, "content", msg)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, str):
                parts.append(p)
            elif isinstance(p, dict) and "text" in p:
                parts.append(p["text"])
        return "".join(parts).strip()
    return str(content)
