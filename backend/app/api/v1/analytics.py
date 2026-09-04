from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.aggregation_schemas import AnalyticsMetricsResponse
from app.services.analytics_aggregation import compute_full_analytics

router = APIRouter()

@router.get("/metrics", response_model=AnalyticsMetricsResponse)
async def get_analytics_metrics(session: AsyncSession = Depends(get_db)):
    """Aggregate recovery dashboard metrics."""
    return await compute_full_analytics(session)
