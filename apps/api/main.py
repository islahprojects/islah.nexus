from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

APP_NAME = "islah.nexus living spine api"
DATA_DIR = Path(os.getenv("ISLAH_DATA_DIR", Path(__file__).resolve().parent / "data"))
WAL_PATH = DATA_DIR / "wal.jsonl"
BOM_PATH = DATA_DIR / "bom.json"
COMMITMENTS_PATH = DATA_DIR / "commitments.jsonl"

SIGMA_MAX = 0.93
APERTURE = 0.07
WALANG_MAIIWAN_FLOOR = 0.05

app = FastAPI(title="ISLAH.NEXUS Living Spine", version="0.1.0")


class BridgeIngest(BaseModel):
    source: str = Field(default="browser")
    commitment: str = Field(..., min_length=8)
    ciphertext: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ButterflyFragment(BaseModel):
    text: str = Field(..., min_length=1)
    source_cluster: str = Field(default="manual")
    privacy_mode: str = Field(default="private_until_sealed")
    implementation_type: str = Field(default="memory")


class ClassifyRequest(BaseModel):
    fragment_id: str
    classification: str
    confidence: float = Field(default=0.93, ge=0.0, le=0.93)
    rewritten_grounded_form: str = Field(..., min_length=1)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_data_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not WAL_PATH.exists():
        WAL_PATH.write_text("", encoding="utf-8")
    if not COMMITMENTS_PATH.exists():
        COMMITMENTS_PATH.write_text("", encoding="utf-8")
    if not BOM_PATH.exists():
        BOM_PATH.write_text(json.dumps(default_bom(), indent=2), encoding="utf-8")


def canonical_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    ensure_data_files()
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row: Dict[str, Any]) -> None:
    ensure_data_files()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(row) + "\n")


def append_wal(event_type: str, payload: Dict[str, Any], redaction_status: str = "clean") -> Dict[str, Any]:
    ensure_data_files()
    events = read_jsonl(WAL_PATH)
    prev_hash = events[-1]["event_hash"] if events else "GENESIS"
    payload_hash = sha256_text(canonical_json(payload))
    event = {
        "event_id": f"wal_{uuid4().hex}",
        "event_type": event_type,
        "timestamp": utc_now(),
        "payload_hash": payload_hash,
        "prev_hash": prev_hash,
        "redaction_status": redaction_status,
        "integrity_sealed": True,
        "payload": payload,
    }
    event["event_hash"] = sha256_text(canonical_json({k: v for k, v in event.items() if k != "event_hash"}))
    append_jsonl(WAL_PATH, event)
    return event


def verify_wal_chain() -> Dict[str, Any]:
    events = read_jsonl(WAL_PATH)
    prev_hash = "GENESIS"
    for index, event in enumerate(events):
        if event.get("prev_hash") != prev_hash:
            return {"valid": False, "count": len(events), "failed_at": index, "reason": "prev_hash_mismatch"}
        supplied = event.get("event_hash")
        computed = sha256_text(canonical_json({k: v for k, v in event.items() if k != "event_hash"}))
        if supplied != computed:
            return {"valid": False, "count": len(events), "failed_at": index, "reason": "event_hash_mismatch"}
        prev_hash = supplied
    return {"valid": True, "count": len(events), "head": prev_hash}


def default_bom() -> Dict[str, Any]:
    return {
        "butterfly_id": "BUTTERFLY_BOM_V1",
        "status": "cocoon_active",
        "constraints": {
            "sigma_max": SIGMA_MAX,
            "uncertainty_aperture": APERTURE,
            "walang_maiiwan_floor": WALANG_MAIIWAN_FLOOR,
            "ai_role": "compass_never_core",
            "glasswing_mode": "defensive_only",
        },
        "source_clusters": ["PANTHEON_ROUTER_SEAL", "BUTTERFLY_BOM_V1"],
        "fragments": [],
        "wings": {
            "left": [],
            "right": [],
            "body": [],
            "antennae": [],
            "cocoon": [],
            "flight_path": [],
            "glasswing": [],
        },
        "dashboard_cards": [
            {"card_id": "system_integrity", "label": "System Integrity", "state_binding": "sigma_bounded", "privacy_mode": "public", "display_copy": "sigma within bounded range"},
            {"card_id": "walang_maiiwan", "label": "Walang Maiiwan", "state_binding": "critical_fragment_retention", "privacy_mode": "public", "display_copy": "critical fragments retained"},
            {"card_id": "butterfly", "label": "Butterfly", "state_binding": "bom_status", "privacy_mode": "public", "display_copy": "BOM ready / Cocoon active"},
            {"card_id": "glasswing", "label": "Glasswing", "state_binding": "defensive_boundary_status", "privacy_mode": "public", "display_copy": "defensive-only boundary active"},
        ],
        "open_questions": [],
    }


def load_bom() -> Dict[str, Any]:
    ensure_data_files()
    return json.loads(BOM_PATH.read_text(encoding="utf-8"))


def save_bom(bom: Dict[str, Any]) -> None:
    ensure_data_files()
    BOM_PATH.write_text(json.dumps(bom, indent=2, ensure_ascii=False), encoding="utf-8")


@app.on_event("startup")
def startup() -> None:
    ensure_data_files()
    if not read_jsonl(WAL_PATH):
        append_wal(
            "WAL_CLASSIFY_FRAGMENT",
            {
                "source_fragments": ["PANTHEON_ROUTER_SEAL", "BUTTERFLY_BOM_V1"],
                "redaction_status": "clean",
                "integrity_sealed": True,
            },
        )


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "service": APP_NAME, "timestamp": utc_now(), "state": "living_spine_active"}


@app.get("/laws")
def laws() -> Dict[str, Any]:
    return {
        "no_lie_policy": "absolute",
        "system_separation": "AI1 gate and Aeterna partner system never merge",
        "browser": "portal",
        "backend": "brain",
        "wal": "proof",
        "sigma": {"min_exclusive": 0, "max": SIGMA_MAX, "aperture": APERTURE},
        "walang_maiiwan_floor": WALANG_MAIIWAN_FLOOR,
        "ai_role": "compass_never_core",
        "glasswing": "defensive_only",
    }


@app.get("/mirror/anna/status")
def anna_status() -> Dict[str, Any]:
    return {"name": "ANNA", "role": "representative_mirror", "status": "online", "authority": "not_core"}


@app.get("/butterfly/status")
def butterfly_status() -> Dict[str, Any]:
    bom = load_bom()
    return {"butterfly_id": bom["butterfly_id"], "status": bom.get("status", "unknown"), "fragments": len(bom.get("fragments", []))}


@app.get("/butterfly/bom")
def butterfly_bom() -> Dict[str, Any]:
    return load_bom()


@app.post("/butterfly/ingest")
def butterfly_ingest(fragment: ButterflyFragment) -> Dict[str, Any]:
    bom = load_bom()
    fragment_id = f"frag_{uuid4().hex}"
    item = {
        "fragment_id": fragment_id,
        "short_label": fragment.text[:48],
        "source_cluster": fragment.source_cluster,
        "classification": "cocoon",
        "secondary_classifications": [],
        "confidence": "likely",
        "status": "pending",
        "privacy_mode": fragment.privacy_mode,
        "implementation_type": fragment.implementation_type,
        "keep_or_merge_or_archive": "needs_review",
        "rewritten_grounded_form": "pending classification",
        "risk_flags": [],
        "promotion_requirements": ["WAL_CLASSIFY_FRAGMENT"],
    }
    bom.setdefault("fragments", []).append(item)
    bom["wings"].setdefault("cocoon", []).append(fragment_id)
    save_bom(bom)
    wal = append_wal("WAL_COCOON_ARCHIVE", {"fragment_id": fragment_id, "source_cluster": fragment.source_cluster}, redaction_status="metadata_only")
    return {"accepted": True, "fragment_id": fragment_id, "wal_event": wal["event_id"]}


@app.post("/butterfly/classify")
def butterfly_classify(request: ClassifyRequest) -> Dict[str, Any]:
    valid_wings = {"left", "right", "body", "antennae", "cocoon", "flight_path", "glasswing"}
    if request.classification not in valid_wings:
        raise HTTPException(status_code=400, detail="invalid classification")
    bom = load_bom()
    fragments = bom.setdefault("fragments", [])
    target = next((f for f in fragments if f.get("fragment_id") == request.fragment_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="fragment not found")
    target["classification"] = request.classification
    target["confidence"] = min(request.confidence, SIGMA_MAX)
    target["status"] = "active_build"
    target["rewritten_grounded_form"] = request.rewritten_grounded_form
    for wing_items in bom.setdefault("wings", {}).values():
        if isinstance(wing_items, list) and request.fragment_id in wing_items:
            wing_items.remove(request.fragment_id)
    bom["wings"].setdefault(request.classification, []).append(request.fragment_id)
    save_bom(bom)
    wal = append_wal("WAL_CLASSIFY_FRAGMENT", {"fragment_id": request.fragment_id, "classification": request.classification, "confidence": target["confidence"]})
    return {"classified": True, "fragment_id": request.fragment_id, "wal_event": wal["event_id"]}


@app.post("/bridge/ingest")
def bridge_ingest(payload: BridgeIngest) -> Dict[str, Any]:
    row = {
        "commitment_id": f"commit_{uuid4().hex}",
        "timestamp": utc_now(),
        "source": payload.source,
        "commitment": payload.commitment,
        "ciphertext_present": bool(payload.ciphertext),
        "metadata_hash": sha256_text(canonical_json(payload.metadata)),
    }
    append_jsonl(COMMITMENTS_PATH, row)
    wal = append_wal("WAL_LOCAL_CHECKPOINT", {"commitment_id": row["commitment_id"], "commitment": payload.commitment}, redaction_status="hash_only")
    return {"accepted": True, "commitment_id": row["commitment_id"], "wal_event": wal["event_id"]}


@app.get("/wal/verify")
def wal_verify() -> Dict[str, Any]:
    return verify_wal_chain()


@app.get("/glasswing/status")
def glasswing_status() -> Dict[str, Any]:
    return {
        "mode": "defensive_only",
        "allowed": ["passive_inbound_monitoring", "integrity_alerts", "wal_proof", "boundary_checks", "secret_redaction"],
        "blocked": ["unauthorized_scanning", "stealth_telemetry", "fake_data_generation", "exploit_behavior", "credential_harvesting"],
        "status": "boundary_active",
    }
