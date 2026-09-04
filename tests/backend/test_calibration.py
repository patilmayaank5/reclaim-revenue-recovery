from app.domain.interventions.schemas import CalibrationInput, InterventionType
from app.domain.interventions.calibration import calibrate_probability

def test_calibration_missing_ai_probability():
    inp = CalibrationInput(
        intervention_type=InterventionType.SMART_RETRY,
        diagnosis_category="insufficient_funds",
        ai_recovery_probability=None
    )
    res = calibrate_probability(inp)
    assert res == 6000 # baseline

def test_calibration_ai_adjustment_within_bounds():
    inp = CalibrationInput(
        intervention_type=InterventionType.SMART_RETRY,
        diagnosis_category="insufficient_funds",
        ai_recovery_probability=0.65 # 6500 bps
    )
    # baseline 6000. diff = +500. Result should be 6500.
    res = calibrate_probability(inp)
    assert res == 6500

def test_calibration_ai_adjustment_capped_positive():
    inp = CalibrationInput(
        intervention_type=InterventionType.SMART_RETRY,
        diagnosis_category="insufficient_funds",
        ai_recovery_probability=0.80 # 8000 bps
    )
    # baseline 6000. diff = +2000. Cap at +1000. Result 7000.
    res = calibrate_probability(inp)
    assert res == 7000

def test_calibration_ai_adjustment_capped_negative():
    inp = CalibrationInput(
        intervention_type=InterventionType.SMART_RETRY,
        diagnosis_category="insufficient_funds",
        ai_recovery_probability=0.20 # 2000 bps
    )
    # baseline 6000. diff = -4000. Cap at -1000. Result 5000.
    res = calibrate_probability(inp)
    assert res == 5000

def test_calibration_absolute_bounds():
    inp = CalibrationInput(
        intervention_type=InterventionType.DUNNING_EMAIL, # dummy baseline e.g. 500, wait, it's 2000
        diagnosis_category="insufficient_funds",
        ai_recovery_probability=0.0
    )
    # diff = -2000. Cap = -1000. Result 1000.
    res = calibrate_probability(inp)
    assert res == 1000
