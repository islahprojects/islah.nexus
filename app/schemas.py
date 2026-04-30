from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Consent(BaseModel):
    allowed: bool = False
    purpose: str = ""
    retention: str = "local_first"


class SealRequest(BaseModel):
    payload: dict[str, Any]


class VerifyRequest(BaseModel):
    payload: dict[str, Any]
    proof: dict[str, Any]


class BridgeIngestRequest(BaseModel):
    dot_id_hash: str = Field(..., min_length=1)
    source: str = "browser_mirror"
    kind: str = "mirror_event"
    ciphertext: str
    commitment_hash: str
    consent: Consent


class BridgeQueryRequest(BaseModel):
    dot_id_hash: str
    query: str
    consent: Consent
    n: int = Field(default=5, ge=1, le=25)


class SyncCommitmentRequest(BaseModel):
    dot_id_hash: str
    mirror_id: str
    action_type: str
    ciphertext: str
    commitment_hash: str
    timestamp: str
    local_sequence: int
    consent: Consent


class ApiRegistration(BaseModel):
    api_name: str
    url: str | None = None
    method: str = "POST"
    auth_env: str | None = None


class ApiCall(BaseModel):
    api: str
    query: str | None = None
    body: dict[str, Any] = Field(default_factory=dict)


class ApiCombineRequest(BaseModel):
    dot_id_hash: str
    need: str
    consent: Consent
    prompt: str = ""
    synthesize: bool = True
    calls: list[ApiCall]


class Theorem4Request(BaseModel):
    dot_id_hash: str
    task: str
    critical_fragments: list[str] = Field(default_factory=list)
    max_cycles: int = Field(default=4, ge=1, le=10)
    perturbation_target: float = 0.382
    return_trace: bool = True


class WiseVoidReflectRequest(BaseModel):
    dot_id_hash: str
    input: str
    mode: Literal["reflect"] = "reflect"
    consent: Consent


class WiseVoidSealRequest(BaseModel):
    dot_id_hash: str
    reflection: dict[str, Any]
    consent: Consent
