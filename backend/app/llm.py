"""
AIVOA LLM Client — Groq-hosted model wrapper via langchain-groq.

Primary model : openai/gpt-oss-120b
Fallback model: openai/gpt-oss-20b

NOTE:
The assignment originally specified gemma2-9b-it (deprecated by Groq Oct 2025,
recommended replacement llama-3.1-8b-instant), but llama-3.1-8b-instant returns
404 on our current Groq account tier. Therefore, we use openai/gpt-oss-120b as
primary instead — another Groq-hosted production model with strong extraction and
reasoning quality — with openai/gpt-oss-20b as a fast, lightweight fallback.

Usage:
    from app.llm import get_llm, get_resilient_llm

    llm = get_resilient_llm()                        # Auto-falls back from primary to fallback
    llm = get_llm()                                  # Primary (openai/gpt-oss-120b)
    llm = get_llm(model="openai/gpt-oss-20b")        # Explicit fallback
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load .env from the backend directory with override enabled
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

# Supported models:
# Primary: High-parameter model with superior extraction & QA triage reasoning
# Fallback: Efficient, lower-latency model on the same Groq infrastructure
PRIMARY_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "openai/gpt-oss-20b"
SUPPORTED_MODELS = {
    PRIMARY_MODEL,
    FALLBACK_MODEL,
    "qwen/qwen3.8-27b",
    "qwen/qwen3.6-27b",
}


def get_llm(
    model: str = PRIMARY_MODEL,
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> ChatGroq:
    """
    Return a ChatGroq instance bound to the requested model.

    Args:
        model:       Model identifier on Groq. Defaults to openai/gpt-oss-120b.
        temperature: Sampling temperature (0 = deterministic, 1 = creative).
        max_tokens:  Maximum tokens in the completion.

    Raises:
        ValueError:  If GROQ_API_KEY is not set or invalid.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY is not configured. "
            "Set it in backend/.env before using the LLM client."
        )

    if model not in SUPPORTED_MODELS:
        raise ValueError(
            f"Unsupported model '{model}'. "
            f"Choose from: {', '.join(sorted(SUPPORTED_MODELS))}"
        )

    return ChatGroq(
        model=model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def get_primary_llm(**kwargs) -> ChatGroq:
    """Convenience: return the primary model (openai/gpt-oss-120b)."""
    return get_llm(model=PRIMARY_MODEL, **kwargs)


def get_fallback_llm(**kwargs) -> ChatGroq:
    """Convenience: return the fallback model (openai/gpt-oss-20b)."""
    return get_llm(model=FALLBACK_MODEL, **kwargs)


def get_resilient_llm(**kwargs):
    """
    Return a resilient LLM runnable that automatically tries the primary model
    (openai/gpt-oss-120b) and seamlessly falls back to the fallback model
    (openai/gpt-oss-20b) if the primary experiences rate-limits or downtime.
    """
    primary = get_primary_llm(**kwargs)
    fallback = get_fallback_llm(**kwargs)
    return primary.with_fallbacks([fallback])
