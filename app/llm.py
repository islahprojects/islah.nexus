from __future__ import annotations

import httpx

from app.config import settings
from app.memory import hash_embedding


async def generate(prompt: str) -> str:
    if settings.OLLAMA_BASE_URL:
        try:
            async with httpx.AsyncClient(timeout=12) as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
                    json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
                return response.json().get("response", "").strip() or fallback_response(prompt)
        except Exception:
            return fallback_response(prompt)
    return fallback_response(prompt)


def fallback_response(prompt: str) -> str:
    return f"Deterministic fallback: {prompt[:240]}"


async def embed(text: str) -> list[float]:
    if settings.OLLAMA_BASE_URL:
        try:
            async with httpx.AsyncClient(timeout=12) as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/embeddings",
                    json={"model": settings.OLLAMA_EMBED_MODEL, "prompt": text},
                )
                response.raise_for_status()
                embedding = response.json().get("embedding")
                if isinstance(embedding, list) and embedding:
                    return [float(x) for x in embedding]
        except Exception:
            pass
    return hash_embedding(text)
