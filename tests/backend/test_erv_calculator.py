import pytest
from app.domain.interventions.schemas import ERVCalculationParams
from app.domain.interventions.erv_calculator import calculate_erv

def test_erv_probability_bounds():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        calculate_erv(ERVCalculationParams(
            probability_bps=-1,
            recoverable_amount_minor=1000,
            intervention_cost_minor=0,
            risk_penalty_minor=0
        ))

    with pytest.raises(ValidationError):
        calculate_erv(ERVCalculationParams(
            probability_bps=10001,
            recoverable_amount_minor=1000,
            intervention_cost_minor=0,
            risk_penalty_minor=0
        ))

def test_erv_zero_probability():
    res = calculate_erv(ERVCalculationParams(
        probability_bps=0,
        recoverable_amount_minor=1000,
        intervention_cost_minor=50,
        risk_penalty_minor=0
    ))
    assert res.expected_recovery_minor == 0
    assert res.erv_minor == -50

def test_erv_max_probability():
    res = calculate_erv(ERVCalculationParams(
        probability_bps=10000,
        recoverable_amount_minor=1000,
        intervention_cost_minor=50,
        risk_penalty_minor=0
    ))
    assert res.expected_recovery_minor == 1000
    assert res.erv_minor == 950

def test_erv_mid_probability():
    res = calculate_erv(ERVCalculationParams(
        probability_bps=5000,
        recoverable_amount_minor=1000,
        intervention_cost_minor=50,
        risk_penalty_minor=10
    ))
    assert res.expected_recovery_minor == 500
    assert res.erv_minor == 440

def test_erv_negative_preserved():
    res = calculate_erv(ERVCalculationParams(
        probability_bps=1000, # 10%
        recoverable_amount_minor=100, # 10 expected
        intervention_cost_minor=500, # 500 cost
        risk_penalty_minor=0
    ))
    assert res.expected_recovery_minor == 10
    assert res.erv_minor == -490
