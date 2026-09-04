from app.domain.interventions.schemas import CalibrationInput, InterventionType

def get_baseline_probability_bps(diagnosis_category: str, intervention_type: InterventionType) -> int:
    """Returns deterministic baseline probability in basis points."""
    # Simplified mock baselines for Phase 5 testing.
    # A real system would use dynamic data or deeper rules.
    baselines = {
        "insufficient_funds": {
            InterventionType.SMART_RETRY: 6000,
            InterventionType.PAYMENT_LINK: 4000,
            InterventionType.DUNNING_EMAIL: 2000,
            InterventionType.MANUAL_REVIEW: 5000,
        },
        "expired_card": {
            InterventionType.PAYMENT_LINK: 5000,
            InterventionType.DUNNING_EMAIL: 3000,
            InterventionType.MANUAL_REVIEW: 5000,
        },
        "invalid_details": {
            InterventionType.PAYMENT_LINK: 4500,
            InterventionType.DUNNING_EMAIL: 2500,
            InterventionType.MANUAL_REVIEW: 5000,
        },
        "fraud_suspected": {
            InterventionType.MANUAL_REVIEW: 5000,
        }
    }

    category_baselines = baselines.get(diagnosis_category, {})
    return category_baselines.get(intervention_type, 1000) # Default fallback


def get_intervention_costs_minor(intervention_type: InterventionType) -> tuple[int, int]:
    """Returns (intervention_cost_minor, risk_penalty_minor) deterministically."""
    # Dummy deterministic costs
    costs = {
        InterventionType.SMART_RETRY: (5, 10), # 0.05 cost, 0.10 risk
        InterventionType.PAYMENT_LINK: (10, 0),
        InterventionType.DUNNING_EMAIL: (1, 0),
        InterventionType.MANUAL_REVIEW: (500, 0) # e.g. 5.00 manual ops cost
    }
    return costs.get(intervention_type, (0, 0))


def calibrate_probability(params: CalibrationInput) -> int:
    """Combines deterministic baseline with bounded AI advisory probability."""
    baseline_bps = get_baseline_probability_bps(params.diagnosis_category, params.intervention_type)

    if params.ai_recovery_probability is None:
        return baseline_bps

    # Apply bounding
    ai_bps = int(params.ai_recovery_probability * 10000)
    difference = ai_bps - baseline_bps

    bounded_adjustment = max(-1000, min(1000, difference))
    final_bps = baseline_bps + bounded_adjustment

    return max(0, min(10000, final_bps))
