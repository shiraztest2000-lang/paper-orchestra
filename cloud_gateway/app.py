"""SHZ PaperOrchestra cloud inference gateway.

The desktop app authenticates with a user access token. Provider API credentials
remain on this server and are never returned to clients.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, ConfigDict

APP_TITLE = "SHZ PaperOrchestra Cloud Gateway"
app = FastAPI(title=APP_TITLE, version="0.1.0")

origins = [x.strip() for x in os.getenv("SHZ_CORS_ORIGINS", "").split(",") if x.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

def _token_hashes() -> dict[str, str]:
    """Read user_id:sha256(token) entries; raw user tokens are not stored."""
    result: dict[str, str] = {}
    for item in os.getenv("SHZ_GATEWAY_TOKEN_HASHES", "").split(","):
        item = item.strip()
        if ":" not in item:
            continue
        user_id, digest = item.split(":", 1)
        if user_id.strip() and len(digest.strip()) == 64:
            result[user_id.strip()] = digest.strip().lower()
    return result

def _authenticate(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="A SHZ account access token is required.")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Invalid access token.")
    supplied = hashlib.sha256(token.encode("utf-8")).hexdigest()
    for user_id, expected in _token_hashes().items():
        if hmac.compare_digest(supplied, expected):
            return user_id
    raise HTTPException(status_code=401, detail="Invalid access token.")

def _client() -> OpenAI:
    api_key = os.getenv("SHZ_UPSTREAM_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="Cloud inference is not configured by the server administrator.")
    options: dict[str, Any] = {
        "api_key": api_key,
        "timeout": float(os.getenv("SHZ_UPSTREAM_TIMEOUT", "120")),
        "max_retries": 1,
    }
    base_url = os.getenv("SHZ_UPSTREAM_BASE_URL", "").strip()
    if base_url:
        options["base_url"] = base_url
    return OpenAI(**options)

class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    model: str
    messages: list[dict[str, Any]]

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "shz-paperorchestra-cloud-gateway"}

@app.get("/v1/models")
def list_models(user_id: str = Depends(_authenticate)) -> dict[str, Any]:
    try:
        return _client().models.list().model_dump()
    except HTTPException:
        raise
    except Exception:
        # Do not expose upstream credentials, URLs, or raw provider errors.
        raise HTTPException(status_code=502, detail="The upstream model service is unavailable.")

@app.post("/v1/chat/completions")
async def chat_completions(
    payload: ChatRequest,
    request: Request,
    user_id: str = Depends(_authenticate),
) -> dict[str, Any]:
    body = await request.json()
    if body.get("stream"):
        raise HTTPException(status_code=400, detail="Streaming is not enabled in this gateway version.")
    try:
        response = _client().chat.completions.create(**body)
        return response.model_dump()
    except HTTPException:
        raise
    except Exception:
        # Never return provider exception text; it can contain sensitive details.
        raise HTTPException(status_code=502, detail="The upstream model request failed.")
