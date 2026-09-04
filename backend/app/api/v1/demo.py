from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.api.deps import get_db
from app.services.demo.scenarios import get_scenarios
from app.services.demo.demo_service import run_scenario, reset_demo

router = APIRouter(prefix="/demo", tags=["demo"])

@router.get("/scenarios")
async def list_scenarios() -> Dict[str, Any]:
    return {"scenarios": get_scenarios()}

@router.post("/scenarios/{scenario_id}/run")
async def execute_scenario(scenario_id: str, session: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    try:
        result = await run_scenario(session, scenario_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset")
async def demo_reset(session: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    try:
        await reset_demo(session)
        return {"status": "Demo reset successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def demo_status(session: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    from sqlalchemy import select, func
    from app.models.case import Case
    from app.services.demo.demo_service import DEMO_MERCHANT_EXTERNAL_ID
    from app.models.merchant import Merchant

    merch_stmt = select(Merchant.id).where(Merchant.external_id == DEMO_MERCHANT_EXTERNAL_ID)
    merch_res = await session.execute(merch_stmt)
    merchant_id = merch_res.scalar_one_or_none()

    if not merchant_id:
        return {"is_active": False, "demo_cases_count": 0}

    case_stmt = select(func.count(Case.id)).where(Case.merchant_id == merchant_id)
    case_res = await session.execute(case_stmt)
    count = case_res.scalar_one()

    return {"is_active": True, "demo_cases_count": count}
