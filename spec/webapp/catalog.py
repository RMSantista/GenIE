"""Catalog of selectable LLM models exposed to the web UI."""

from typing import Any, Dict, List, Optional

MODELS: List[Dict[str, Any]] = [
    {
        "id": "gemini-2.5-flash",
        "provider": "google",
        "provider_label": "Google",
        "label": "Gemini 2.5 Flash",
        "note": "rápido · multimodal",
    },
    {
        "id": "gemini-2.5-pro",
        "provider": "google",
        "provider_label": "Google",
        "label": "Gemini 2.5 Pro",
        "note": "raciocínio profundo",
    },
    {
        "id": "gpt-4o-mini",
        "provider": "openai",
        "provider_label": "OpenAI",
        "label": "GPT-4o mini",
        "note": "barato · estruturado",
    },
    {
        "id": "gpt-4o",
        "provider": "openai",
        "provider_label": "OpenAI",
        "label": "GPT-4o",
        "note": "multimodal · alta qualidade",
    },
    {
        "id": "claude-sonnet-4-6",
        "provider": "anthropic",
        "provider_label": "Anthropic",
        "label": "Claude Sonnet 4.6",
        "note": "raciocínio + extração",
    },
    {
        "id": "claude-haiku-4-5-20251001",
        "provider": "anthropic",
        "provider_label": "Anthropic",
        "label": "Claude Haiku 4.5",
        "note": "rápido · econômico",
    },
]


def find_model(model_id: str) -> Optional[Dict[str, Any]]:
    """Look up a catalog entry by model id.

    Args:
        model_id: Catalog model id

    Returns:
        Optional[dict]: Catalog entry or None
    """

    return next((m for m in MODELS if m["id"] == model_id), None)
