import json
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from apps.api.core.database import get_db
from apps.api.dependencies import get_current_user, get_organization, record_audit
from apps.api.models.entities import Document, DocumentVersion, User
from apps.api.schemas.api import DocumentListResponse, DocumentResponse, DocumentVersionResponse
from apps.api.services.storage import storage_service

router = APIRouter(tags=["Documents"])


def _document_to_response(doc: Document) -> DocumentResponse:
    current = doc.versions[-1] if doc.versions else None
    return DocumentResponse(
        id=doc.id,
        organization_id=doc.organization_id,
        workspace_id=doc.workspace_id,
        title=doc.title,
        document_type=doc.document_type,
        language=doc.language,
        status=doc.status,
        metadata=doc.metadata_json or {},
        created_by=doc.created_by,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        current_version=DocumentVersionResponse.model_validate(current) if current else None,
    )


@router.get("/organizations/{org_id}/documents", response_model=DocumentListResponse)
def list_documents(
    org_id: UUID,
    workspace_id: UUID | None = None,
    document_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    get_organization(org_id, current_user, db)
    query = db.query(Document).filter(
        Document.organization_id == org_id,
        Document.deleted_at.is_(None),
    ).options(joinedload(Document.versions))
    if workspace_id:
        query = query.filter(Document.workspace_id == workspace_id)
    if document_type:
        query = query.filter(Document.document_type == document_type)

    total = query.count()
    docs = (
        query.order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    for doc in docs:
        doc.versions  # noqa: B018 — load relationship

    return DocumentListResponse(
        items=[_document_to_response(d) for d in docs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/organizations/{org_id}/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(
    org_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: str = Form("other"),
    language: str = Form("fa"),
    workspace_id: str | None = Form(None),
    metadata: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    get_organization(org_id, current_user, db)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    storage_key, content_hash = storage_service.upload(
        org_id, file.filename or "upload.bin", content, file.content_type or "application/octet-stream"
    )

    meta = json.loads(metadata) if metadata else {}
    ws_id = UUID(workspace_id) if workspace_id else None

    document = Document(
        organization_id=org_id,
        workspace_id=ws_id,
        title=title,
        document_type=document_type,
        language=language,
        status="ready",
        metadata_json=meta,
        created_by=current_user.id,
    )
    db.add(document)
    db.flush()

    version = DocumentVersion(
        document_id=document.id,
        version_number=1,
        file_name=file.filename or "upload.bin",
        file_size=len(content),
        content_type=file.content_type or "application/octet-stream",
        content_hash=content_hash,
        storage_key=storage_key,
    )
    db.add(version)
    db.commit()
    db.refresh(document)
    document.versions = [version]

    record_audit(
        db,
        organization_id=org_id,
        user=current_user,
        action="document.upload",
        resource_type="document",
        resource_id=document.id,
        metadata={"title": title, "file_name": version.file_name},
        ip_address=request.client.host if request.client else None,
    )

    return _document_to_response(document)


@router.get("/organizations/{org_id}/documents/{document_id}", response_model=DocumentResponse)
def get_document(
    org_id: UUID,
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    get_organization(org_id, current_user, db)
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.organization_id == org_id, Document.deleted_at.is_(None))
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return _document_to_response(doc)


@router.delete("/organizations/{org_id}/documents/{document_id}", status_code=204)
def delete_document(
    org_id: UUID,
    document_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    from datetime import UTC, datetime

    get_organization(org_id, current_user, db)
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.organization_id == org_id, Document.deleted_at.is_(None))
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    doc.deleted_at = datetime.now(UTC)
    db.commit()

    record_audit(
        db,
        organization_id=org_id,
        user=current_user,
        action="document.delete",
        resource_type="document",
        resource_id=document_id,
        ip_address=request.client.host if request.client else None,
    )


@router.get("/organizations/{org_id}/documents/{document_id}/versions", response_model=dict)
def list_document_versions(
    org_id: UUID,
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    get_organization(org_id, current_user, db)
    versions = (
        db.query(DocumentVersion)
        .join(Document)
        .filter(Document.id == document_id, Document.organization_id == org_id)
        .order_by(DocumentVersion.version_number.desc())
        .all()
    )
    return {"items": [DocumentVersionResponse.model_validate(v) for v in versions]}


@router.get("/organizations/{org_id}/documents/{document_id}/download")
def download_document(
    org_id: UUID,
    document_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    get_organization(org_id, current_user, db)
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.organization_id == org_id, Document.deleted_at.is_(None))
        .first()
    )
    if doc is None or not doc.versions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    version = sorted(doc.versions, key=lambda v: v.version_number, reverse=True)[0]
    try:
        data, content_type = storage_service.download(version.storage_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found in storage") from exc

    record_audit(
        db,
        organization_id=org_id,
        user=current_user,
        action="document.download",
        resource_type="document",
        resource_id=document_id,
        ip_address=request.client.host if request.client else None,
    )

    return Response(
        content=data,
        media_type=content_type or version.content_type,
        headers={"Content-Disposition": f'attachment; filename="{version.file_name}"'},
    )
