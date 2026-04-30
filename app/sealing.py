from __future__ import annotations

import hashlib
import hmac
import json
import time
from pathlib import Path
from typing import Any

from app.config import settings

ALGORITHM = "CNSI-SHA512-HMAC-SHA512-v1"
GENESIS_HASH = "genesis-000"


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha512_hex(text: str) -> str:
    return hashlib.sha512(text.encode("utf-8")).hexdigest()


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ensure_vault() -> None:
    settings.vault_path.mkdir(parents=True, exist_ok=True)
    settings.wal_path.touch(exist_ok=True)


def last_wal_hash() -> str:
    ensure_vault()
    last = GENESIS_HASH
    for line in settings.wal_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            last = json.loads(line)["proof"]["proof_hash"]
    return last


def compute_proof(payload: dict[str, Any], prev_hash: str = GENESIS_HASH) -> dict[str, Any]:
    payload_hash = sha512_hex(canonical_json(payload))
    signature = hmac.new(settings.FOUNDERS_SEED.encode("utf-8"), payload_hash.encode("utf-8"), hashlib.sha512).hexdigest()
    proof_body = {
        "algorithm": ALGORITHM,
        "hash": payload_hash,
        "hmac": signature,
        "prev_hash": prev_hash,
        "signer": "islah.nexus",
        "timestamp_ms": int(time.time() * 1000),
        "wal_pointer": "wal://pending",
    }
    proof_body["proof_hash"] = sha256_hex(canonical_json(proof_body))
    return proof_body


def append_wal(payload: dict[str, Any]) -> dict[str, Any]:
    ensure_vault()
    prev_hash = last_wal_hash()
    proof = compute_proof(payload, prev_hash)
    proof["wal_pointer"] = f"wal://local/{int(time.time() * 1000)}-{proof['proof_hash'][:12]}"
    proof["proof_hash"] = sha256_hex(canonical_json({k: v for k, v in proof.items() if k != "proof_hash"}))
    entry = {"proof": proof, "payload": payload}
    with settings.wal_path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(entry) + "\n")
    return entry


def verify_proof(payload: dict[str, Any], proof: dict[str, Any]) -> bool:
    payload_hash = sha512_hex(canonical_json(payload))
    expected_hmac = hmac.new(settings.FOUNDERS_SEED.encode("utf-8"), payload_hash.encode("utf-8"), hashlib.sha512).hexdigest()
    if payload_hash != proof.get("hash") or expected_hmac != proof.get("hmac"):
        return False
    proof_without_hash = {k: v for k, v in proof.items() if k != "proof_hash"}
    return sha256_hex(canonical_json(proof_without_hash)) == proof.get("proof_hash")


def wal_tail(n: int = 20) -> list[dict[str, Any]]:
    ensure_vault()
    rows = [json.loads(line) for line in settings.wal_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows[-n:]


def verify_wal() -> dict[str, Any]:
    ensure_vault()
    prev_hash = GENESIS_HASH
    entries = wal_tail(1_000_000)
    for index, entry in enumerate(entries):
        proof = entry.get("proof", {})
        payload = entry.get("payload", {})
        if proof.get("prev_hash") != prev_hash:
            return {"valid": False, "broken_at": index, "reason": "prev_hash_mismatch"}
        if not verify_proof(payload, proof):
            return {"valid": False, "broken_at": index, "reason": "proof_mismatch"}
        prev_hash = proof.get("proof_hash")
    return {"valid": True, "count": len(entries), "head": prev_hash}
