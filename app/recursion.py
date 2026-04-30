from __future__ import annotations

from app.objective import critical_inclusion_score, score_objective, scs_metric
from app.sealing import append_wal


def run_theorem4(task: str, critical_fragments: list[str], max_cycles: int = 4, perturbation_target: float = 0.382, mutate: bool = False, return_trace: bool = True) -> dict:
    max_cycles = max(1, min(int(max_cycles), 10))
    trace = []
    candidate = f"Stabilize: {task}. Preserve: {', '.join(critical_fragments)}."

    for cycle in range(1, max_cycles + 1):
        inc = critical_inclusion_score(candidate, critical_fragments)
        coh = min(0.93, 0.55 + cycle * 0.07)
        rel = min(0.93, 0.60 + cycle * 0.05)
        nov = max(0.05, 0.22 - cycle * 0.01)
        uncertainty = max(0.07, 0.25 - cycle * 0.025)
        drift = max(0.03, 0.18 - cycle * 0.02)
        objective = score_objective(coh, rel, nov, inc)
        scs = scs_metric(coh, rel, uncertainty, drift, nov, perturbation_target)
        trace.append({"cycle": cycle, "coherence": coh, "relevance": rel, "novelty": nov, "inclusion": inc, "uncertainty": uncertainty, "drift": drift, "objective": objective, "scs": scs})
        candidate = f"{candidate} Cycle {cycle}: objective={objective:.3f}, inclusion={inc:.3f}, scs={scs:.3f}."

    result = {
        "task": task,
        "bounded": True,
        "max_cycles": max_cycles,
        "cycles_run": len(trace),
        "critical_fragments_preserved": critical_inclusion_score(candidate, critical_fragments) >= 0.93 if critical_fragments else True,
        "result_preview": candidate[:900],
        "trace": trace if return_trace else [],
    }
    proof = append_wal({"type": "theorem4.run" if mutate else "theorem4.predict", "summary": {k: v for k, v in result.items() if k != "trace"}})
    result["sealed_proof_hash"] = proof["proof"]["proof_hash"]
    return result


def theorem4_status() -> dict:
    return {"status": "bounded", "max_cycles_hard_limit": 10, "no_background_loops": True, "no_self_executing_generated_code": True}
