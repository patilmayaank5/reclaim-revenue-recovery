import uuid
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.deps import get_db
from app.models.audit_event import AuditEvent
from app.models.enums import AuditEventType

router = APIRouter()

class AuditEventItem(BaseModel):
    id: uuid.UUID
    event_type: str
    entity_id: uuid.UUID
    actor: str
    summary: str
    event_data: dict | None
    created_at: datetime

class AuditEventsResponse(BaseModel):
    items: list[AuditEventItem]
    total: int
    limit: int
    offset: int

@router.get("/events", response_model=AuditEventsResponse)
async def get_audit_events(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    event_type: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = None,
    session: AsyncSession = Depends(get_db)
):
    """Retrieve chronologically ordered audit logs."""

    stmt = select(AuditEvent).order_by(desc(AuditEvent.created_at))
    count_stmt = select(func.count(AuditEvent.id))

    if event_type:
        try:
            ev_enum = AuditEventType(event_type)
            stmt = stmt.where(AuditEvent.event_type == ev_enum)
            count_stmt = count_stmt.where(AuditEvent.event_type == ev_enum)
        except ValueError:
            # If invalid event_type, return empty
            return {"items": [], "total": 0, "limit": limit, "offset": offset}

    if entity_id:
        stmt = stmt.where(AuditEvent.entity_id == entity_id)
        count_stmt = count_stmt.where(AuditEvent.entity_id == entity_id)

    total_res = await session.execute(count_stmt)
    total = total_res.scalar() or 0

    stmt = stmt.limit(limit).offset(offset)
    events_res = await session.execute(stmt)
    events = events_res.scalars().all()

    items = []
    for evt in events:
        items.append(AuditEventItem(
            id=evt.id,
            event_type=evt.event_type.value,
            entity_id=evt.entity_id,
            actor=evt.actor,
            summary=evt.summary,
            event_data=evt.event_data,
            created_at=evt.created_at
        ))

    return AuditEventsResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset
    )
