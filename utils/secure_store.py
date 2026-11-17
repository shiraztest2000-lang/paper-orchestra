"""Windows-backed secret storage for SHZ PaperOrchestra.

API credentials are stored in the current Windows user's Credential Manager via
the keyring package. They are never written to the application's .env file.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

SERVICE_NAME = "SHZ PaperOrchestra"
SECRET_ENV_KEYS = (
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "GROQ_API_KEY",
    "CEREBRAS_API_KEY",
    "DEEPSEEK_API_KEY",
    "TOGETHER_API_KEY",
    "SHZ_LLM_API_KEY",
    "SEMANTIC_SCHOLAR_API_KEY",
)
SECRET_SET = frozenset(SECRET_ENV_KEYS)


def _backend():
    try:
        import keyring
    except ImportError as exc:
        raise RuntimeError(
            "ماژول ذخیره امن ویندوز نصب نیست. برنامه را به‌روزرسانی یا دوباره نصب کنید."
        ) from exc
    return keyring


def load_secure_secrets() -> dict[str, str]:
    """Load credentials from the current user's OS credential store."""
    backend = _backend()
    values: dict[str, str] = {}
    for name in SECRET_ENV_KEYS:
        value = backend.get_password(SERVICE_NAME, name)
        if value:
            values[name] = value
    return values


def save_secure_secrets(values: Mapping[str, str]) -> None:
    """Persist non-empty credentials in the OS credential store."""
    backend = _backend()
    for name in SECRET_ENV_KEYS:
        value = str(values.get(name, "") or "").strip()
        if value:
            backend.set_password(SERVICE_NAME, name, value)


def migrate_legacy_env(env_path: str | os.PathLike[str]) -> bool:
    """Move legacy plaintext API keys from .env into OS storage.

    Returns True if a migration occurred. The original file is rewritten only
    after every discovered secret has been stored successfully.
    """
    path = Path(env_path)
    if not path.is_file():
        return False

    lines = path.read_text(encoding="utf-8").splitlines()
    secrets: dict[str, str] = {}
    kept: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            kept.append(line)
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if name in SECRET_SET:
            secrets[name] = value.strip().strip('"').strip("'")
        else:
            kept.append(line)

    if not secrets:
        return False

    save_secure_secrets(secrets)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("\n".join(kept).rstrip() + "\n", encoding="utf-8")
    os.replace(temporary, path)
    return True
