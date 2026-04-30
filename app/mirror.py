from __future__ import annotations

from app.sealing import append_wal

WISE_VOID_IDENTITY = {
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
    "seal": "◉ Walang Maiiwan",
}


def extract_fragments(text: str) -> list[str]:
    words = [word.strip(".,!?;:()[]{}\"'").lower() for word in text.split()]
    important = [word for word in words if len(word) >= 5]
    return list(dict.fromkeys(important[:7]))


def reflect(input_text: str) -> dict:
    fragments = extract_fragments(input_text)
    next_step = "Turn the strongest fragment into one WAL-sealed build step."
    if "api" in input_text.lower() or "bridge" in input_text.lower():
        next_step = "Verify consent, seal the API call summary, then expose only dashboard-safe status."
    return {
        "mirror": "wise_void",
        "identity": WISE_VOID_IDENTITY,
        "reflection": input_text.strip()[:700],
        "critical_fragments": fragments,
        "suggested_next_step": next_step,
        "seal_available": True,
        "walang_maiiwan_check": True,
    }


def seal_reflection(reflection: dict) -> dict:
    return append_wal({"type": "wise_void.reflection", "reflection": reflection})
