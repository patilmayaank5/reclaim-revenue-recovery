from pydantic import BaseModel

class DemoScenarioDef(BaseModel):
    scenario_id: str
    name: str
    amount_minor: int
    failure_code: str
    is_experiment: bool = False

SCENARIOS = [
    DemoScenarioDef(
        scenario_id="scenario_1",
        name="Auto Recovery (ALLOW_AUTO)",
        amount_minor=800_00, # ₹800
        failure_code="insufficient_funds"
    ),
    DemoScenarioDef(
        scenario_id="scenario_2",
        name="Human Approval (REQUIRE_APPROVAL)",
        amount_minor=4800_000, # ₹48,000 - inherently exceeds 2,000,000 threshold
        failure_code="technical_failure"
    ),
    DemoScenarioDef(
        scenario_id="scenario_3",
        name="Terminal Stop",
        amount_minor=500_00,
        failure_code="revoked_mandate" # Terminal failure
    ),
    DemoScenarioDef(
        scenario_id="scenario_4",
        name="Experiment Fixture (90 Treatment / 10 Holdout)",
        amount_minor=1000_00, # ₹1,000
        failure_code="insufficient_funds",
        is_experiment=True
    )
]

def get_scenarios() -> list[dict]:
    return [s.model_dump() for s in SCENARIOS]
