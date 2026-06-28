from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from apps.api.core.database import get_db
from apps.api.dependencies import get_current_user, get_organization, record_audit
from apps.api.models.entities import CollectionDocument, Document, KnowledgeCollection, User
from apps.api.schemas.api import (
    CreateCollectionRequest,
    KnowledgeCollectionResponse,
    UpdateCollectionRequest,
)

router = APIRouter(tags=["Collections"])


def _collection_response(collection: KnowledgeCollection, db: Session) -> KnowledgeCollectionResponse:
    count = db.query(CollectionDocument).filter(CollectionDocument.collection_id == collection.id).count()
    return KnowledgeCollectionResponse(
        id=collection.id,
        organization_id=collection.organization_id,
        workspace_id=collection.workspace_id,
        name=collection.name,
        description=collection.description,
        legal_domain_id=collection.legal_domain_id,
        document_count=count,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


@router.get("/organizations/{org_id}/collections", response_model=dict)
def list_collections(
    org_id: UUID,
    workspace_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    get_organization(org_id, current_user, db)
    query = db.query(KnowledgeCollection).filter(KnowledgeCollection.organization_id == org_id)
    if workspace_id:
        query = query.filter(KnowledgeCollection.workspace_id == workspace_id)
    collections = query.order_by(KnowledgeCollection.created_at.desc()).all()
    return {"items": [_collection_response(c, db) for c in collections]}


@router.post("/organizations/{org_id}/collections", response_model=KnowledgeCollectionResponse, status_code=201)
def create_collection(
    org_id: UUID,
    payload: CreateCollectionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> KnowledgeCollectionResponse:
    get_organization(org_id, current_user, db)
    collection = KnowledgeCollection(
        organization_id=org_id,
        workspace_id=payload.workspace_id,
        name=payload.name,
        description=payload.description,
        legal_domain_id=payload.legal_domain_id,
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)

    record_audit(
        db,
        organization_id=org_id,
        user=current_user,
        action="collection.create",
        resource_type="collection",
        resource_id=collection.id,
        metadata={"name": collection.name},
        ip_address=request.client.host if request.client else None,
    )

    return _collection_response(collection, db)


@router.get("/organizations/{org_id}/collections/{collection_id}", response_model=KnowledgeCollectionResponse)
def get_collection(
    org_id: UUID,
    collection_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> KnowledgeCollectionResponse:
    get_organization(org_id, current_user, db)
    collection = (
        db.query(KnowledgeCollection)
        .filter(KnowledgeCollection.id == collection_id, KnowledgeCollection.organization_id == org_id)
        .first()
    )
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    return _collection_response(collection, db)


@router.patch("/organizations/{org_id}/collections/{collection_id}", response_model=KnowledgeCollectionResponse)
def update_collection(
    org_id: UUID,
    collection_id: UUID,
    payload: UpdateCollectionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> KnowledgeCollectionResponse:
    get_organization(org_id, current_user, db)
    collection = (
        db.query(KnowledgeCollection)
        .filter(KnowledgeCollection.id == collection_id, KnowledgeCollection.organization_id == org_id)
        .first()
    )
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    if payload.name is not None:
        collection.name = payload.name
    if payload.description is not None:
        collection.description = payload.description
    db.commit()
    db.refresh(collection)

    record_audit(
        db,
        organization_id=org_id,
        user=current_user,
        action="collection.update",
        resource_type="collection",
        resource_id=collection.id,
        ip_address=request.client.host if request.client else None,
    )

    return _collection_response(collection, db)


@router.post("/organizations/{org_id}/collections/{collection_id}/documents", status_code=204)
def add_document_to_collection(
    org_id: UUID,
    collection_id: UUID,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    get_organization(org_id, current_user, db)
    document_id = UUID(body["document_id"])

    collection = (
        db.query(KnowledgeCollection)
        .filter(KnowledgeCollection.id == collection_id, KnowledgeCollection.organization_id == org_id)
        .first()
    )
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.organization_id == org_id, Document.deleted_at.is_(None))
        .first()
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    existing = (
        db.query(CollectionDocument)
        .filter(CollectionDocument.collection_id == collection_id, CollectionDocument.document_id == document_id)
        .first()
    )
    if existing is None:
        db.add(CollectionDocument(collection_id=collection_id, document_id=document_id))
        db.commit()


@router.delete("/organizations/{org_id}/collections/{collection_id}/documents", status_code=204)
def remove_document_from_collection(
    org_id: UUID,
    collection_id: UUID,
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    get_organization(org_id, current_user, db)
    db.query(CollectionDocument).filter(
        CollectionDocument.collection_id == collection_id,
        CollectionDocument.document_id == document_id,
    ).delete()
    db.commit()
