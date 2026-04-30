from __future__ import annotations

from app.chi2mm import AETHEL_DAMPING


def clamp(value: float, low: float = 0.0, high: float = 0.93) -> float:
    return max(low, min(high, float(value)))


def score_objective(coh: float, rel: float, nov: float, inc: float, alpha: float = 0.35, beta: float = 0.30, gamma: float = 0.15, mu: float = 0.20) -> float:
    return clamp(alpha * coh + beta * rel + gamma * nov + mu * inc)


def scs_metric(coherence: float, relevance: float, uncertainty: float, drift: float, novelty: float, damping: float = AETHEL_DAMPING) -> float:
    brain_pressure = coherence + relevance
    shadow_pressure = uncertainty + drift + novelty
    epsilon = 1e-9
    return clamp(damping / (brain_pressure + shadow_pressure + epsilon))


def critical_inclusion_score(text: str, critical_fragments: list[str]) -> float:
    if not critical_fragments:
        return 0.93
    lower = text.lower()
    hits = sum(1 for fragment in critical_fragments if fragment.lower() in lower)
    return clamp(hits / len(critical_fragments), low=0.05)
