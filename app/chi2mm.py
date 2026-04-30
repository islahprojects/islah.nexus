L0 = 1.0
OMEGA = 1.0
SIGMA_MAX = 0.93
UNCERTAINTY_APERTURE = 0.07
WALANG_MAIIWAN_FLOOR = 0.05
AETHEL_DAMPING = 0.382


def clamp_sigma(value: float) -> float:
    return max(0.0, min(SIGMA_MAX, float(value)))


def invariants() -> dict:
    return {
        "love_invariant_L0": L0,
        "unity_invariant_omega": OMEGA,
        "sigma_max": SIGMA_MAX,
        "uncertainty_aperture": UNCERTAINTY_APERTURE,
        "walang_maiiwan_floor": WALANG_MAIIWAN_FLOOR,
        "aethel_damping": AETHEL_DAMPING,
    }
