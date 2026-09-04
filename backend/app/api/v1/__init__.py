from fastapi import APIRouter

from app.api.v1.ingestion import router as ingestion_router
from app.api.v1.cases import router as cases_router
from app.api.v1.ai import router as ai_router
from app.api.v1.interventions import router as interventions_router
from app.api.v1.policy import router as policy_router
from app.api.v1.actions import router as actions_router
from app.api.v1.execution import router as execution_router
from app.api.v1.verifications import router as verifications_router
from app.api.v1.overview import router as overview_router
from app.api.v1.experiments import router as experiments_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.policies_api import router as policies_api_router
from app.api.v1.audit_api import router as audit_api_router
from app.api.v1.demo import router as demo_router

api_router = APIRouter()

api_router.include_router(demo_router)

api_router.include_router(
    ingestion_router,
    prefix="/ingestion",
    tags=["Ingestion"],
)

api_router.include_router(
    cases_router,
    prefix="/cases",
    tags=["Cases"],
)

api_router.include_router(
    ai_router,
    prefix="/ai",
    tags=["AI Diagnosis"],
)

api_router.include_router(
    interventions_router,
    tags=["Interventions"],
)

api_router.include_router(
    policy_router,
    tags=["Policy Engine"],
)

api_router.include_router(
    actions_router,
    tags=["Action Workflow"],
)

api_router.include_router(
    execution_router,
    tags=["Execution Engine"],
)

api_router.include_router(
    verifications_router,
    tags=["Verification Engine"],
)

api_router.include_router(
    overview_router,
    tags=["Overview Metrics"],
)

api_router.include_router(
    experiments_router,
    prefix="/experiments",
    tags=["Experiments"],
)

api_router.include_router(
    analytics_router,
    prefix="/analytics",
    tags=["Analytics"],
)

api_router.include_router(
    policies_api_router,
    prefix="/policies",
    tags=["Policies"],
)

api_router.include_router(
    audit_api_router,
    prefix="/audit",
    tags=["Audit"],
)
