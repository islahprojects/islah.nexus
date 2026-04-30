from __future__ import annotations

import json
import math
import time
from uuid import uuid4

from app.config import settings
from app.sealing import append_wal, canonical_json, sha256_hex


def ensure_memory() -> None:
    settings.vault_path.mkdir(parents=True, exist_ok=True)
    settings.memory_path.touch(exist_ok=True)


def hash_embedding(text: str, dims: int = 32) -> list[float]:
    digest = sha256_hex(text)
    values = []
    for i in range(dims):
        chunk = digest[(i * 2) % len(digest):((i * 2) % len(digest)) + 2]
        values.append(int(chunk, 16) / 255.0)
    return values


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def add_memory(text: str, tags: list[str] | None = None, source: str = "manual") -> dict:
    ensure_memory()
    preview = text if settings.DEV_PLAINTEXT_MODE else text[:120]
    payload = {"type": "memory.add", "source": source, "text_preview": preview, "tags": tags or []}
    proof = append_wal(payload)["proof"]
    record = {
        "id": f"mem_{uuid4().hex}",
        "text_preview": preview,
        "embedding": hash_embedding(text),
        "score": 1.0,
        "tags": tags or [],
        "source": source,
        "created_at": int(time.time()),
        "sealed_proof_hash": proof["proof_hash"],
    }
    with settings.memory_path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(record) + "\n")
    prune_memory()
    return record


def all_memory() -> list[dict]:
    ensure_memory()
    return [json.loads(line) for line in settings.memory_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def search_memory(query: str, n: int = 5) -> list[dict]:
    q = hash_embedding(query)
    rows = all_memory()
    scored = []
    for row in rows:
        row = dict(row)
        row["score"] = cosine(q, row.get("embedding", []))
        scored.append(row)
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:n]


def prune_memory() -> None:
    rows = all_memory()
    if len(rows) <= settings.MAX_MEMORY_RECORDS:
        return
    rows = rows[-settings.MAX_MEMORY_RECORDS:]
    settings.memory_path.write_text("\n".join(canonical_json(row) for row in rows) + "\n", encoding="utf-8")
