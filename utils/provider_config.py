"""Cloud-only provider configuration for SHZ PaperOrchestra."""
from __future__ import annotations
import os
from typing import Any
from urllib.parse import urlparse

HOSTED_DEFAULTS = {
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "deepseek": "https://api.deepseek.com",
    "groq": "https://api.groq.com/openai/v1",
    "together": "https://api.together.xyz/v1",
}
OPENAI_COMPATIBLE_PROVIDERS = {"shz-cloud", "openai", "openai-compatible", "openrouter", "deepseek", "groq", "together", "vllm-cloud"}
LEGACY_LOCAL_PROVIDERS = {"ollama", "lmstudio", "lm-studio", "local-ollama"}

def get_provider() -> str:
    provider = os.getenv("SHZ_LLM_PROVIDER", "gemini").strip().lower()
    return {"lm-studio": "lmstudio", "local-ollama": "ollama"}.get(provider, provider)

def get_base_url(provider: str | None = None) -> str | None:
    provider = (provider or get_provider()).strip().lower()
    if provider == "shz-cloud":
        configured = os.getenv("SHZ_CLOUD_BASE_URL", "").strip() or os.getenv("SHZ_LLM_BASE_URL", "").strip()
        return configured.rstrip("/") if configured else None
    configured = os.getenv("SHZ_LLM_BASE_URL", "").strip()
    return configured.rstrip("/") if configured else HOSTED_DEFAULTS.get(provider)

def is_local_provider(provider: str | None = None) -> bool:
    return (provider or get_provider()).strip().lower() in LEGACY_LOCAL_PROVIDERS

def is_openai_compatible(provider: str | None = None) -> bool:
    return (provider or get_provider()).strip().lower() in OPENAI_COMPATIBLE_PROVIDERS

def get_api_key(provider: str | None = None) -> str | None:
    provider = (provider or get_provider()).strip().lower()
    names = {"shz-cloud": "SHZ_CLOUD_ACCESS_TOKEN", "openai": "OPENAI_API_KEY", "openrouter": "OPENROUTER_API_KEY", "deepseek": "DEEPSEEK_API_KEY", "groq": "GROQ_API_KEY", "together": "TOGETHER_API_KEY"}
    key_name = names.get(provider)
    return os.getenv(key_name) or os.getenv("SHZ_LLM_API_KEY") or (os.getenv("OPENAI_API_KEY") if provider == "openai-compatible" else None)

def validate_provider_config(provider: str | None = None) -> tuple[bool, str]:
    provider = (provider or get_provider()).strip().lower()
    if provider in LEGACY_LOCAL_PROVIDERS:
        return False, "Local models are disabled. Choose a cloud provider; no AI model is installed on this PC."
    if provider == "gemini":
        if os.getenv("GEMINI_API_KEY") or (os.getenv("VERTEX_AI_PROJECT") and os.getenv("VERTEX_AI_LOCATION")):
            return True, "Gemini cloud configuration is ready."
        return False, "Gemini API key or complete Vertex AI configuration is required."
    if not is_openai_compatible(provider):
        return False, f"Unsupported cloud provider: {provider}"
    url = get_base_url(provider)
    if not url:
        return False, "Cloud endpoint URL is required."
    if not get_api_key(provider):
        return False, "An access token or API key is required."
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False, "Invalid cloud endpoint URL."
    if provider == "shz-cloud" and parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1"}:
        return False, "The SHZ central cloud gateway must use HTTPS."
    return True, "Cloud provider configuration is ready."

def list_compatible_models(provider: str | None = None, timeout: float = 10.0) -> list[str]:
    import requests
    provider = (provider or get_provider()).strip().lower()
    valid, message = validate_provider_config(provider)
    if not valid:
        raise ValueError(message)
    base_url = get_base_url(provider)
    headers = {"Authorization": f"Bearer {get_api_key(provider)}"}
    response = requests.get(f"{base_url}/models", headers=headers, timeout=timeout)
    response.raise_for_status()
    payload: dict[str, Any] = response.json()
    return sorted({str(item["id"]) for item in payload.get("data", []) if isinstance(item, dict) and item.get("id")})

def test_compatible_connection(provider: str | None = None, timeout: float = 10.0) -> tuple[bool, str]:
    try:
        models = list_compatible_models(provider, timeout)
        if not models:
            return False, "Connected, but the cloud provider returned no models."
        return True, f"Cloud connection successful; {len(models)} models found."
    except Exception as exc:
        return False, f"Cloud connection failed: {exc}"
