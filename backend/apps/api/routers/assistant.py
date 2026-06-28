from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from apps.api.core.database import get_db
from apps.api.dependencies import get_current_user, get_organization, record_audit
from apps.api.models.entities import AIMessage, AISession, User
from apps.api.schemas.api import (
    AIMessageResponse,
    AISessionDetailResponse,
    AISessionResponse,
    AISessionScope,
    CreateAISessionRequest,
    SendMessageRequest,
)
from apps.api.services.llm import generate_assistant_reply

router = APIRouter(tags=["Assistant"])


def _session_response(session: AISession) -> AISessionResponse:
    scope_data = session.scope_json or {}
    return AISessionResponse(
        id=session.id,
        organization_id=session.organization_id,
        workspace_id=session.workspace_id,
        title=session.title,
        legal_domain_id=session.legal_domain_id,
        scope=AISessionScope(
            document_ids=[UUID(x) for x in scope_data.get("document_ids", [])],
            collection_ids=[UUID(x) for x in scope_data.get("collection_ids", [])],
        ),
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("/organizations/{org_id}/assistant/sessions", response_model=dict)
def list_sessions(
    org_id: UUID,
    workspace_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    get_organization(org_id, current_user, db)
    query = db.query(AISession).filter(AISession.organization_id == org_id)
    if workspace_id:
        query = query.filter(AISession.workspace_id == workspace_id)
    sessions = query.order_by(AISession.updated_at.desc()).all()
    return {"items": [_session_response(s) for s in sessions]}


@router.post("/organizations/{org_id}/assistant/sessions", response_model=AISessionResponse, status_code=201)
def create_session(
    org_id: UUID,
    payload: CreateAISessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AISessionResponse:
    get_organization(org_id, current_user, db)
    session = AISession(
        organization_id=org_id,
        workspace_id=payload.workspace_id,
        title=payload.title,
        legal_domain_id=payload.legal_domain_id,
        scope_json={
            "document_ids": [str(x) for x in payload.scope.document_ids],
            "collection_ids": [str(x) for x in payload.scope.collection_ids],
        },
        created_by=current_user.id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_response(session)


@router.get("/organizations/{org_id}/assistant/sessions/{session_id}", response_model=AISessionDetailResponse)
def get_session(
    org_id: UUID,
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AISessionDetailResponse:
    get_organization(org_id, current_user, db)
    session = (
        db.query(AISession)
        .filter(AISession.id == session_id, AISession.organization_id == org_id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    messages = (
        db.query(AIMessage)
        .filter(AIMessage.session_id == session_id)
        .order_by(AIMessage.created_at.asc())
        .all()
    )

    base = _session_response(session)
    return AISessionDetailResponse(
        **base.model_dump(),
        messages=[
            AIMessageResponse(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                citations=m.citations_json or [],
                model_version=m.model_version,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.post("/organizations/{org_id}/assistant/sessions/{session_id}/messages", response_model=AIMessageResponse)
def send_message(
    org_id: UUID,
    session_id: UUID,
    payload: SendMessageRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIMessageResponse:
    get_organization(org_id, current_user, db)
    session = (
        db.query(AISession)
        .filter(AISession.id == session_id, AISession.organization_id == org_id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    user_message = AIMessage(session_id=session_id, role="user", content=payload.content)
    db.add(user_message)
    db.flush()

    prior = (
        db.query(AIMessage)
        .filter(AIMessage.session_id == session_id, AIMessage.id != user_message.id)
        .order_by(AIMessage.created_at.asc())
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in prior if m.role in ("user", "assistant")]

    result = generate_assistant_reply(
        payload.content,
        legal_domain_id=session.legal_domain_id,
        history=history,
    )
    model_version = f"ollama/{result.get('model', 'unknown')}"

    assistant_message = AIMessage(
        session_id=session_id,
        role="assistant",
        content=result["content"],
        citations_json=[],
        model_version=model_version,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    record_audit(
        db,
        organization_id=org_id,
        user=current_user,
        action="assistant.message",
        resource_type="ai_session",
        resource_id=session_id,
        metadata={"message_length": len(payload.content), "model": result.get("model")},
        ip_address=request.client.host if request.client else None,
    )

    return AIMessageResponse(
        id=assistant_message.id,
        session_id=assistant_message.session_id,
        role=assistant_message.role,
        content=assistant_message.content,
        citations=[],
        model_version=assistant_message.model_version,
        created_at=assistant_message.created_at,
    )
