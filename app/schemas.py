from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

RetentionMode = Literal["local_first", "local_only", "session_only", "redacted_public"]
MirrorMode = Literal["reflect"]
HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


class Consent(BaseModel):
    allowed: bool = False
    purpose: str = Field(default="", max_length=120)
    retention: RetentionMode = "local_first"

    @model_validator(mode="after")
    def require_purpose_when_allowed(self) -> "Consent":
        if self.allowed and not self.purpose.strip():
            raise ValueError("consent purpose is required when allowed=true")
        return self


class SealRequest(BaseModel):
    payload: dict[str, Any] = Field(..., min_length=1)


class VerifyRequest(BaseModel):
    payload: dict[str, Any]
    proof: dict[str, Any]


class BridgeIngestRequest(BaseModel):
    dot_id_hash: str = Field(..., min_length=1, max_length=160)
    source: str = Field(default="browser_mirror", max_length=80)
    kind: str = Field(default="mirror_event", max_length=80)
    ciphertext: str = Field(..., min_length=1)
    commitment_hash: str = Field(..., min_length=32, max_length=256)
    consent: Consent

    @field_validator("ciphertext")
    @classmethod
    def no_plaintext_marker(cls, value: str) -> str:
        if value.strip().startswith("{") or value.strip().startswith("["):
            raise ValueError("ciphertext must not look like plaintext JSON")
        return value


class BridgeQueryRequest(BaseModel):
    dot_id_hash: str = Field(..., min_length=1, max_length=160)
    query: str = Field(..., min_length=1, max_length=1000)
    consent: Consent
    n: int = Field(default=5, ge=1, le=25)


class SyncCommitmentRequest(BaseModel):
    dot_id_hash: str = Field(..., min_length=1, max_length=160)
    mirror_id: str = Field(..., min_length=1, max_length=120)
    action_type: str = Field(..., min_length=1, max_length=120)
    ciphertext: str = Field(..., min_length=1)
    commitment_hash: str = Field(..., min_length=32, max_length=256)
    timestamp: str = Field(..., min_length=1, max_length=80)
    local_sequence: int = Field(..., ge=1)
    consent: Consent


class ApiRegistration(BaseModel):
    api_name: str = Field(..., min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    url: str | None = Field(default=None, max_length=2000)
    method: HttpMethod = "POST"
    auth_env: str | None = Field(default=None, max_length=120)


class ApiCall(BaseModel):
    api: str = Field(..., min_length=1, max_length=120)
    query: str | None = Field(default=None, max_length=1000)
    body: dict[str, Any] = Field(default_factory=dict)


class ApiCombineRequest(BaseModel):
    dot_id_hash: str = Field(..., min_length=1, max_length=160)
    need: str = Field(..., min_length=1, max_length=240)
    consent: Consent
    prompt: str = Field(default="", max_length=2000)
    synthesize: bool = True
    calls: list[ApiCall] = Field(..., min_length=1, max_length=8)


class Theorem4Request(BaseModel):
    dot_id_hash: str = Field(..., min_length=1, max_length=160)
    task: str = Field(..., min_length=1, max_length=2000)
    critical_fragments: list[str] = Field(default_factory=list, max_length=25)
    max_cycles: int = Field(default=4, ge=1, le=10)
    perturbation_target: float = Field(default=0.382, ge=0.0, le=1.0)
    return_trace: bool = True


class WiseVoidReflectRequest(BaseModel):
    dot_id_hash: str = Field(..., min_length=1, max_length=160)
    input: str = Field(..., min_length=1, max_length=4000)
    mode: MirrorMode = "reflect"
    consent: Consent


class WiseVoidSealRequest(BaseModel):
    dot_id_hash: str = Field(..., min_length=1, max_length=160)
    reflection: dict[str, Any] = Field(..., min_length=1)
    consent: Consent


class HealthResponse(BaseModel):
    ok: bool
    service: str
    status: str


class WalVerifyResponse(BaseModel):
    valid: bool
    count: int | None = None
    head: str | None = None
    broken_at: int | None = None
    reason: str | None = None
