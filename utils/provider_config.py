"""Provider configuration helpers for cloud and OpenAI-compatible local endpoints."""
from __future__ import annotations
import os
from typing import Any
from urllib.parse import urlparse

LOCAL_DEFAULTS = {"ollama": "http://127.0.0.1:11434/v1", "lmstudio": "http://127.0.0.1:1234/v1"}
HOSTED_DEFAULTS = {"openrouter": "https://openrouter.ai/api/v1", "deepseek": "https://api.deepseek.com", "groq": "https://api.groq.com/openai/v1", "together": "https://api.together.xyz/v1", "openai": "https://api.openai.com/v1"}
OPENAI_COMPATIBLE_PROVIDERS = {"openai", "openai-compatible", "openrouter", "deepseek", "groq", "together", "ollama", "lmstudio", "vllm"}

def get_provider() -> str:
    provider = os.getenv("SHZ_LLM_PROVIDER", "gemini").strip().lower()
    return {"lm-studio": "lmstudio", "local-ollama": "ollama"}.get(provider, provider)

def get_base_url(provider: str | None = None) -> str | None:
    provider = (provider or get_provider()).strip().lower()
    configured = os.getenv("SHZ_LLM_BASE_URL", "").strip()
    return configured.rstrip("/") if configured else LOCAL_DEFAULTS.get(provider) or HOSTED_DEFAULTS.get(provider)

def is_local_provider(provider: str | None = None) -> bool:
    return (provider or get_provider()).strip().lower() in {"ollama", "lmstudio"}

def is_openai_compatible(provider: str | None = None) -> bool:
    return (provider or get_provider()).strip().lower() in OPENAI_COMPATIBLE_PROVIDERS

def get_api_key(provider: str | None = None) -> str | None:
    provider = (provider or get_provider()).strip().lower()
    if is_local_provider(provider):
        return os.getenv("SHZ_LLM_API_KEY") or "local-no-key"
    names = {"openai": "OPENAI_API_KEY", "openrouter": "OPENROUTER_API_KEY", "deepseek": "DEEPSEEK_API_KEY", "groq": "GROQ_API_KEY", "together": "TOGETHER_API_KEY"}
    key_name = names.get(provider)
    return os.getenv(key_name) or os.getenv("SHZ_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")

def validate_provider_config(provider: str | None = None) -> tuple[bool, str]:
    provider = (provider or get_provider()).strip().lower()
    if provider == "gemini":
        if os.getenv("GEMINI_API_KEY") or (os.getenv("VERTEX_AI_PROJECT") and os.getenv("VERTEX_AI_LOCATION")):
            return True, "Gemini configuration is ready."
        return False, "Gemini API key or complete Vertex AI configuration is required."
    if not is_openai_compatible(provider):
        return False, f"Unsupported provider: {provider}"
    url = get_base_url(provider)
    if not url:
        return False, "Provider endpoint is not configured."
    if not is_local_provider(provider) and not get_api_key(provider):
        return False, "An API key is required for this provider."
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False, "Invalid endpoint URL."
    return True, "Provider configuration is ready."

def list_compatible_models(provider: str | None = None, timeout: float = 5.0) -> list[str]:
    import requests
    provider = (provider or get_provider()).strip().lower()
    base_url = get_base_url(provider)
    if not base_url:
        raise ValueError("Provider endpoint is not configured.")
    headers: dict[str, str] = {}
    key = get_api_key(provider)
    if key:
        headers["Authorization"] = f"Bearer {key}"
    response = requests.get(f"{base_url}/models", headers=headers, timeout=timeout)
    response.raise_for_status()
    payload: dict[str, Any] = response.json()
    return sorted({str(item["id"]) for item in payload.get("data", []) if isinstance(item, dict) and item.get("id")})

def test_compatible_connection(provider: str | None = None, timeout: float = 5.0) -> tuple[bool, str]:
    try:
        models = list_compatible_models(provider, timeout)
        if not models:
            return False, "Connected, but no models were returned."
        return True, f"Connection successful; {len(models)} models found."
    except Exception as exc:
        return False, f"Connection failed: {exc}"
