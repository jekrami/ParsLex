from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from apps.api.core.config import settings
from apps.api.core.database import get_db
from apps.api.core.security import create_access_token, get_password_hash, verify_password
from apps.api.dependencies import get_current_user, record_audit
from apps.api.models.entities import User
from apps.api.schemas.api import LoginRequest, LoginResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Identity"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(str(user.id), {"email": user.email, "role": user.role})

    from apps.api.models.entities import Membership

    membership = db.query(Membership).filter(Membership.user_id == user.id).first()
    if membership:
        record_audit(
            db,
            organization_id=membership.organization_id,
            user=user,
            action="login",
            resource_type="user",
            resource_id=user.id,
            ip_address=request.client.host if request.client else None,
        )

    return LoginResponse(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
