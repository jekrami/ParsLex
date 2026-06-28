from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.core.database import get_db
from apps.api.dependencies import get_current_user, get_organization
from apps.api.models.entities import AuditEvent, User
from apps.api.schemas.api import AuditEventListResponse, AuditEventResponse

router = APIRouter(tags=["Audit"])


@router.get("/organizations/{org_id}/audit/events", response_model=AuditEventListResponse)
def list_audit_events(
    org_id: UUID,
    resource_type: str | None = None,
    user_id: UUID | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuditEventListResponse:
    get_organization(org_id, current_user, db)
    query = db.query(AuditEvent).filter(AuditEvent.organization_id == org_id)

    if resource_type:
        query = query.filter(AuditEvent.resource_type == resource_type)
    if user_id:
        query = query.filter(AuditEvent.user_id == user_id)
    if from_date:
        query = query.filter(AuditEvent.created_at >= from_date)
    if to_date:
        query = query.filter(AuditEvent.created_at <= to_date)

    total = query.count()
    events = (
        query.order_by(AuditEvent.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return AuditEventListResponse(
        items=[
            AuditEventResponse(
                id=e.id,
                organization_id=e.organization_id,
                user_id=e.user_id,
                user_email=e.user_email,
                action=e.action,
                resource_type=e.resource_type,
                resource_id=e.resource_id,
                metadata=e.metadata_json or {},
                ip_address=e.ip_address,
                created_at=e.created_at,
            )
            for e in events
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
