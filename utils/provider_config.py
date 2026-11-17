"""Direct cloud-provider configuration for SHZ PaperOrchestra.

No local inference server or SHZ-hosted gateway is used by this desktop build.
"""
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
    "cerebras": "https://api.cerebras.ai/v1",
}
OPENAI_COMPATIBLE_PROVIDERS = {
    "openai", "openai-compatible", "openrouter", "deepseek",
    "groq", "together", "cerebras",
}
LEGACY_LOCAL_PROVIDERS = {"ollama", "lmstudio", "lm-studio", "local-ollama"}
DISABLED_GATEWAY_PROVIDERS = {"shz-cloud", "vllm-cloud"}


def get_provider() -> str:
    provider = os.getenv("SHZ_LLM_PROVIDER", "gemini").strip().lower()
    return {"lm-studio": "lmstudio", "local-ollama": "ollama"}.get(provider, provider)


def get_base_url(provider: str | None = None) -> str | None:
    provider = (provider or get_provider()).strip().lower()
    if provider == "openai-compatible":
        configured = os.getenv("SHZ_LLM_BASE_URL", "").strip()
        return configured.rstrip("/") if configured else None
    return HOSTED_DEFAULTS.get(provider)


def is_local_provider(provider: str | None = None) -> bool:
    return (provider or get_provider()).strip().lower() in LEGACY_LOCAL_PROVIDERS


def is_openai_compatible(provider: str | None = None) -> bool:
    return (provider or get_provider()).strip().lower() in OPENAI_COMPATIBLE_PROVIDERS


def get_api_key(provider: str | None = None) -> str | None:
    provider = (provider or get_provider()).strip().lower()
    names = {
        "openai": "OPENAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "groq": "GROQ_API_KEY",
        "together": "TOGETHER_API_KEY",
        "cerebras": "CEREBRAS_API_KEY",
    }
    key_name = names.get(provider)
    if provider == "openai-compatible":
        return os.getenv("SHZ_LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or None
    return (os.getenv(key_name) or os.getenv("SHZ_LLM_API_KEY")) if key_name else None


def validate_provider_config(provider: str | None = None) -> tuple[bool, str]:
    provider = (provider or get_provider()).strip().lower()
    if provider in LEGACY_LOCAL_PROVIDERS:
        return False, "مدل محلی غیرفعال است؛ یک سرویس ابری مستقیم انتخاب کنید."
    if provider in DISABLED_GATEWAY_PROVIDERS:
        return False, "اتصال به درگاه مرکزی SHZ در این نسخه غیرفعال است؛ یک ارائه‌دهنده ابری مستقیم انتخاب کنید."
    if provider == "gemini":
        if os.getenv("GEMINI_API_KEY") or (
            os.getenv("VERTEX_AI_PROJECT") and os.getenv("VERTEX_AI_LOCATION")
        ):
            return True, "تنظیمات Gemini Cloud آماده است."
        return False, "برای Gemini به کلید API رایگان/پولی Google AI Studio یا تنظیمات کامل Vertex AI نیاز است."
    if not is_openai_compatible(provider):
        return False, f"ارائه‌دهنده ابری پشتیبانی نمی‌شود: {provider}"
    url = get_base_url(provider)
    if not url:
        return False, "نشانی endpoint سرویس ابری لازم است."
    if not get_api_key(provider):
        return False, "کلید API حساب خودتان لازم است؛ رایگان بودن سهمیه به معنی بی‌نیازی از کلید نیست."
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False, "نشانی endpoint معتبر نیست."
    if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1"}:
        return False, "برای اتصال مستقیم به سرویس ابری، HTTPS الزامی است."
    return True, "تنظیمات اتصال مستقیم ابری آماده است."


def list_compatible_models(provider: str | None = None, timeout: float = 15.0) -> list[str]:
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
    return sorted({
        str(item["id"])
        for item in payload.get("data", [])
        if isinstance(item, dict) and item.get("id")
    })


def test_compatible_connection(provider: str | None = None, timeout: float = 15.0) -> tuple[bool, str]:
    try:
        models = list_compatible_models(provider, timeout)
        if not models:
            return False, "اتصال برقرار شد، اما سرویس‌دهنده فهرست مدلی برنگرداند."
        return True, f"اتصال مستقیم ابری موفق بود؛ {len(models)} مدل شناسایی شد."
    except Exception as exc:
        return False, f"اتصال ابری ناموفق بود: {exc}"
