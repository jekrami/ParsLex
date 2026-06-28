from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from apps.api.core.database import get_db
from apps.api.core.security import decode_access_token
from apps.api.models.entities import Membership, Organization, User

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user_id = payload.get("sub")
    user = db.get(User, UUID(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_organization(org_id: UUID, user: User, db: Session) -> Organization:
    membership = (
        db.query(Membership)
        .filter(Membership.organization_id == org_id, Membership.user_id == user.id)
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of organization")
    org = db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


def record_audit(
    db: Session,
    *,
    organization_id: UUID,
    user: User | None,
    action: str,
    resource_type: str,
    resource_id: UUID | None = None,
    metadata: dict | None = None,
    ip_address: str | None = None,
) -> None:
    from apps.api.models.entities import AuditEvent

    event = AuditEvent(
        organization_id=organization_id,
        user_id=user.id if user else None,
        user_email=user.email if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_json=metadata or {},
        ip_address=ip_address,
    )
    db.add(event)
    db.commit()
