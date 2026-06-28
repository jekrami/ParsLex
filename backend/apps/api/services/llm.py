"""LLM service — loads parametric model config and delegates to Ollama."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[4]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.llm.ollama_client import OllamaClient, load_models_config
from apps.api.core.config import settings


@lru_cache
def get_llm_client() -> OllamaClient:
    config = load_models_config(settings.ai_models_config_path)
    config.base_url = settings.ollama_base_url.rstrip("/")
    return OllamaClient(config)


def generate_assistant_reply(
    user_message: str,
    *,
    legal_domain_id: str = "iran-oil-gas",
    history: list[dict[str, str]] | None = None,
) -> dict:
    client = get_llm_client()
    context = f"Active legal domain pack: {legal_domain_id}."
    try:
        return client.chat("assistant", user_message, context=context, history=history)
    except Exception as exc:
        return {
            "content": (
                f"Unable to reach Ollama ({client.config.base_url}). "
                f"Ensure Ollama is running and the model is pulled. Error: {exc}"
            ),
            "model": client.get_task_profile("assistant").model,
            "provider": "ollama",
            "error": str(exc),
        }
