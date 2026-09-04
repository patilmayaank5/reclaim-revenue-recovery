from app.domain.interventions.schemas import ERVCalculationParams, ERVCalculationResult

def calculate_erv(params: ERVCalculationParams) -> ERVCalculationResult:
    """Deterministically calculate Expected Recovery Value (ERV) in minor integer units.

    Formula:
    expected_recovery_minor = (probability_bps * recoverable_amount_minor) // 10000
    ERV = expected_recovery_minor - intervention_cost_minor - risk_penalty_minor

    Negative ERVs are preserved.
    """
    if not (0 <= params.probability_bps <= 10000):
        raise ValueError("probability_bps must be between 0 and 10000")

    expected_recovery_minor = (params.probability_bps * params.recoverable_amount_minor) // 10000
    erv_minor = expected_recovery_minor - params.intervention_cost_minor - params.risk_penalty_minor

    return ERVCalculationResult(
        expected_recovery_minor=expected_recovery_minor,
        erv_minor=erv_minor
    )
