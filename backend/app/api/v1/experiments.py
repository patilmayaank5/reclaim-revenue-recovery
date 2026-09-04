import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.aggregation_schemas import ExperimentSummaryRow, ExperimentDetailResult
from app.services.experiment_aggregation import compute_experiment_list, compute_experiment_detail

router = APIRouter()

@router.get("", response_model=dict)
async def list_experiments(
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_db)
):
    """List experiments with assignment counts."""
    results = await compute_experiment_list(session, status)
    return {"items": [r.model_dump() for r in results], "total": len(results)}


@router.get("/{experiment_id}", response_model=ExperimentDetailResult)
async def get_experiment(
    experiment_id: uuid.UUID,
    session: AsyncSession = Depends(get_db)
):
    """Detailed experiment with cohort metrics, incremental lift, intervention breakdown."""
    result = await compute_experiment_detail(session, experiment_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found."
        )
    return result
