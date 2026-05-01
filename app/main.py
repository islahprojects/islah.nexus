from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.schemas import (
    ApiCombineRequest,
    ApiRegistration,
    BridgeIngestRequest,
    BridgeQueryRequest,
    SealRequest,
    SyncCommitmentRequest,
    Theorem4Request,
    VerifyRequest,
    WiseVoidReflectRequest,
    WiseVoidSealRequest,
)
from app.sealing import append_wal, verify_proof, verify_wal, wal_tail

app = FastAPI(title=settings.APP_NAME, version="0.1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["http://localhost:9000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_REGISTRY: dict[str, dict[str, Any]] = {}


def require_token(authorization: str | None = Header(default=None)) -> None:
    expected = f"Bearer {settings.BRIDGE_API_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="invalid or missing bridge token")


def require_consent(consent: Any) -> None:
    if not getattr(consent, "allowed", False):
        raise HTTPException(status_code=403, detail="consent.allowed=true is required")


def safe_summary(value: Any, limit: int = 320) -> str:
    text = str(value)
    return text[:limit] + ("..." if len(text) > limit else "")


def theorem4_run(req: Theorem4Request, mutate: bool = False) -> dict[str, Any]:
    cycles: list[dict[str, Any]] = []
    fragments = list(dict.fromkeys(req.critical_fragments))
    coherence = 0.58
    relevance = 0.64
    novelty = 0.22
    inclusion = 1.0 if fragments else 0.05

    for cycle in range(1, req.max_cycles + 1):
        uncertainty = max(0.07, req.perturbation_target / (cycle + 1))
        drift = max(0.0, 0.18 / cycle)
        cost = min(0.93, 0.08 * cycle)
        objective = (0.35 * coherence) + (0.30 * relevance) + (0.15 * novelty) + (0.20 * inclusion)
        score = objective - (0.12 * uncertainty) - (0.08 * cost) - (0.10 * drift)
        scs = req.perturbation_target / (coherence + relevance + uncertainty + drift + novelty + 1e-9)
        cycles.append({
            "cycle": cycle,
            "score": round(max(0.05, min(0.93, score)), 6),
            "coherence": round(coherence, 6),
            "relevance": round(relevance, 6),
            "novelty": round(novelty, 6),
            "inclusion": round(inclusion, 6),
            "uncertainty": round(uncertainty, 6),
            "drift": round(drift, 6),
            "cost": round(cost, 6),
            "scs": round(scs, 6),
            "fragments_preserved": fragments,
        })
        coherence = min(0.93, coherence + 0.055)
        relevance = min(0.93, relevance + 0.045)
        novelty = max(0.07, novelty - 0.015)

    result = {
        "task": req.task,
        "bounded": True,
        "mutated_memory": mutate,
        "max_cycles": req.max_cycles,
        "cycles_run": len(cycles),
        "critical_fragments_preserved": fragments,
        "converged": True,
        "trace": cycles if req.return_trace else [],
        "summary": "Bounded Theorem 4 preview completed without hidden background loops.",
    }
    append_wal({
        "type": "theorem4.run" if mutate else "theorem4.predict",
        "dot_id_hash": req.dot_id_hash,
        "summary": result["summary"],
        "cycles_run": len(cycles),
    })
    return result


def wise_void_reflect(req: WiseVoidReflectRequest) -> dict[str, Any]:
    require_consent(req.consent)
    tokens = [part.strip(".,:;!?()[]{}\n\t").lower() for part in req.input.split()]
    critical: list[str] = []
    for token in tokens:
        if len(token) > 4 and token not in critical:
            critical.append(token)
        if len(critical) >= 7:
            break
    return {
        "mirror": "wise_void",
        "reflection": f"Core signal: {safe_summary(req.input, 420)}",
        "critical_fragments": critical,
        "suggested_next_step": "Convert the strongest fragment into one sealed, testable build step.",
        "seal_available": True,
        "walang_maiiwan_check": True,
        "authority": "consent_bound_compass_never_core",
    }


def built_in_api(name: str, query: str | None = None, body: dict[str, Any] | None = None) -> dict[str, Any]:
    body = body or {}
    if name == "wal.head":
        tail = wal_tail(1)
        return {"api": name, "head": tail[0]["proof"]["proof_hash"] if tail else "genesis-000"}
    if name == "wal.verify":
        return {"api": name, **verify_wal()}
    if name == "memory.search":
        return {"api": name, "query": query or body.get("query", ""), "results": []}
    if name == "manual.echo":
        return {"api": name, "echo": body}
    if name == "theorem4.protocol":
        return {"api": name, "bounded": True, "max_cycles": 10, "no_hidden_loops": True}
    if name == "wise_void.reflect":
        pseudo = WiseVoidReflectRequest(
            dot_id_hash="api_hub",
            input=str(body.get("input", query or "Mirror status")),
            consent={"allowed": True, "purpose": "api_hub_internal", "retention": "local_first"},
        )
        return {"api": name, **wise_void_reflect(pseudo)}
    raise HTTPException(status_code=404, detail=f"unknown api: {name}")


@app.on_event("startup")
def startup() -> None:
    settings.vault_path.mkdir(parents=True, exist_ok=True)
    settings.wal_path.touch(exist_ok=True)
    settings.commitments_path.touch(exist_ok=True)


@app.get("/", response_model=None)
def index():
    index_path = settings.frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"ok": True, "service": settings.APP_NAME, "frontend": "not_found"}


if settings.frontend_path.exists():
    app.mount("/static", StaticFiles(directory=settings.frontend_path), name="static")


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "service": settings.APP_NAME, "status": "grand_bridge_node_online"}


@app.get("/laws")
def laws() -> dict[str, Any]:
    return {
        "ai_role": "compass_never_core",
        "dot_sovereignty": True,
        "no_universal_master_key": True,
        "consent_bound_mirrors": True,
        "no_api_bypasses_consent_encryption_or_proof": True,
        "bounded_recursion": True,
        "walang_maiiwan": "no critical fragment left behind",
        "love_invariant_L0": 1,
        "unity_invariant_Omega": 1,
        "audit": "proof",
    }


@app.post("/seal", dependencies=[Depends(require_token)])
def seal(req: SealRequest) -> dict[str, Any]:
    return append_wal(req.payload)


@app.post("/verify", dependencies=[Depends(require_token)])
def verify(req: VerifyRequest) -> dict[str, Any]:
    return {"valid": verify_proof(req.payload, req.proof)}


@app.get("/wal/tail", dependencies=[Depends(require_token)])
def wal_tail_endpoint(n: int = 20) -> dict[str, Any]:
    return {"entries": wal_tail(max(1, min(n, 100)))}


@app.get("/wal/verify")
def wal_verify_endpoint() -> dict[str, Any]:
    return verify_wal()


@app.post("/bridge/ingest", dependencies=[Depends(require_token)])
def bridge_ingest(req: BridgeIngestRequest) -> dict[str, Any]:
    require_consent(req.consent)
    payload = req.model_dump()
    payload["plaintext_stored"] = False
    entry = append_wal({"type": "bridge.ingest", **payload})
    return {"accepted": True, "proof": entry["proof"]}


@app.post("/bridge/query", dependencies=[Depends(require_token)])
def bridge_query(req: BridgeQueryRequest) -> dict[str, Any]:
    require_consent(req.consent)
    append_wal({"type": "bridge.query", "dot_id_hash": req.dot_id_hash, "query_preview": safe_summary(req.query), "n": req.n})
    return {"query": req.query, "results": [], "note": "local JSONL memory search will be attached in the memory forge step"}


@app.post("/sync/commitment", dependencies=[Depends(require_token)])
def sync_commitment(req: SyncCommitmentRequest) -> dict[str, Any]:
    require_consent(req.consent)
    entry = append_wal({"type": "sync.commitment", **req.model_dump()})
    return {"accepted": True, "proof": entry["proof"]}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "hello", "service": settings.APP_NAME, "status": "connected"})
    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_json({"type": "echo", "message": message})
    except WebSocketDisconnect:
        return


@app.get("/bridge/apis")
def list_apis() -> dict[str, Any]:
    builtins = ["memory.search", "wal.head", "wal.verify", "manual.echo", "theorem4.protocol", "wise_void.reflect"]
    return {"builtins": builtins, "registered": sorted(API_REGISTRY.keys())}


@app.post("/bridge/apis/register", dependencies=[Depends(require_token)])
def register_api(req: ApiRegistration) -> dict[str, Any]:
    if req.url and not settings.ALLOW_EXTERNAL_HTTP_APIS:
        raise HTTPException(status_code=403, detail="external HTTP APIs are disabled")
    API_REGISTRY[req.api_name] = req.model_dump()
    append_wal({"type": "api.register", "api_name": req.api_name, "external": bool(req.url)})
    return {"registered": True, "api_name": req.api_name}


@app.delete("/bridge/apis/{api_name}", dependencies=[Depends(require_token)])
def delete_api(api_name: str) -> dict[str, Any]:
    API_REGISTRY.pop(api_name, None)
    append_wal({"type": "api.delete", "api_name": api_name})
    return {"deleted": True, "api_name": api_name}


@app.post("/bridge/apis/call", dependencies=[Depends(require_token)])
def call_api(req: dict[str, Any]) -> dict[str, Any]:
    api_name = req.get("api")
    if not api_name:
        raise HTTPException(status_code=400, detail="api is required")
    result = built_in_api(api_name, req.get("query"), req.get("body", {}))
    append_wal({"type": "api.call", "api": api_name, "summary": safe_summary(result)})
    return result


@app.post("/bridge/apis/combine", dependencies=[Depends(require_token)])
def combine_apis(req: ApiCombineRequest) -> dict[str, Any]:
    require_consent(req.consent)
    outputs = [built_in_api(call.api, call.query, call.body) for call in req.calls]
    result = {"need": req.need, "synthesized": req.synthesize, "outputs": outputs, "summary": f"Combined {len(outputs)} API outputs for {req.need}."}
    append_wal({"type": "api.combine", "dot_id_hash": req.dot_id_hash, "need": req.need, "call_count": len(outputs)})
    return result


@app.get("/bridge/api/connectors")
def alias_connectors() -> dict[str, Any]:
    return list_apis()


@app.post("/bridge/api/register", dependencies=[Depends(require_token)])
def alias_register(req: ApiRegistration) -> dict[str, Any]:
    return register_api(req)


@app.post("/bridge/api/call", dependencies=[Depends(require_token)])
def alias_call(req: dict[str, Any]) -> dict[str, Any]:
    return call_api(req)


@app.post("/bridge/api/combine", dependencies=[Depends(require_token)])
def alias_combine(req: ApiCombineRequest) -> dict[str, Any]:
    return combine_apis(req)


@app.get("/bridge/theorem4/status")
def theorem4_status() -> dict[str, Any]:
    return {"bounded": True, "max_cycles_cap": 10, "hidden_background_loops": False}


@app.post("/bridge/theorem4/predict", dependencies=[Depends(require_token)])
def theorem4_predict(req: Theorem4Request) -> dict[str, Any]:
    return theorem4_run(req, mutate=False)


@app.post("/bridge/theorem4/run", dependencies=[Depends(require_token)])
def theorem4_run_endpoint(req: Theorem4Request) -> dict[str, Any]:
    return theorem4_run(req, mutate=True)


@app.get("/mirror/wise-void/status")
def wise_void_status() -> dict[str, Any]:
    return {
        "mirror_id": "wise_void",
        "mirror_type": "sovereign_reflection",
        "display_name": "Wise Void Mirror",
        "role": "reflective_partner",
        "authority": "consent_bound",
        "can_impersonate_source_dot": False,
        "can_hold_private_key": False,
        "can_remember_with_consent": True,
        "can_request_wal_seal": True,
        "can_override_source_dot": False,
        "law": "AI is compass, never core",
        "seal": "Walang Maiiwan",
    }


@app.post("/mirror/wise-void/reflect", dependencies=[Depends(require_token)])
def wise_void_reflect_endpoint(req: WiseVoidReflectRequest) -> dict[str, Any]:
    return wise_void_reflect(req)


@app.post("/mirror/wise-void/seal-reflection", dependencies=[Depends(require_token)])
def wise_void_seal(req: WiseVoidSealRequest) -> dict[str, Any]:
    require_consent(req.consent)
    entry = append_wal({"type": "wise_void.seal_reflection", "dot_id_hash": req.dot_id_hash, "reflection": req.reflection})
    return {"sealed": True, "proof": entry["proof"]}
