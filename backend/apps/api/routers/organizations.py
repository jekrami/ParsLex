from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.core.database import get_db
from apps.api.dependencies import get_current_user, get_organization
from apps.api.models.entities import Membership, Organization, User, Workspace
from apps.api.schemas.api import OrganizationResponse, WorkspaceResponse

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("", response_model=dict)
def list_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    orgs = (
        db.query(Organization)
        .join(Membership, Membership.organization_id == Organization.id)
        .filter(Membership.user_id == current_user.id)
        .all()
    )
    return {
        "items": [OrganizationResponse.model_validate(o) for o in orgs],
        "total": len(orgs),
    }


@router.get("/{org_id}/workspaces", response_model=dict)
def list_workspaces(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    get_organization(org_id, current_user, db)
    workspaces = db.query(Workspace).filter(Workspace.organization_id == org_id).all()
    return {
        "items": [WorkspaceResponse.model_validate(w) for w in workspaces],
    }
