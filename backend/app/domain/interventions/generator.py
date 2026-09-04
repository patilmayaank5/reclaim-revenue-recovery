from app.domain.interventions.schemas import InterventionType

def get_applicable_interventions(diagnosis_category: str) -> list[InterventionType]:
    """Deterministically identifies which intervention types are logical for a failure category."""

    mapping = {
        "insufficient_funds": [
            InterventionType.SMART_RETRY,
            InterventionType.PAYMENT_LINK,
            InterventionType.DUNNING_EMAIL,
            InterventionType.MANUAL_REVIEW
        ],
        "expired_card": [
            InterventionType.PAYMENT_LINK,
            InterventionType.DUNNING_EMAIL,
            InterventionType.MANUAL_REVIEW
        ],
        "invalid_details": [
            InterventionType.PAYMENT_LINK,
            InterventionType.DUNNING_EMAIL,
            InterventionType.MANUAL_REVIEW
        ],
        "fraud_suspected": [
            InterventionType.MANUAL_REVIEW
        ]
    }

    return mapping.get(diagnosis_category, [])
