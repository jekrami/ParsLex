from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    legal_domain_id: str | None = None

    model_config = {"from_attributes": True}


class DocumentVersionResponse(BaseModel):
    id: UUID
    document_id: UUID
    version_number: int
    file_name: str
    file_size: int
    content_type: str
    content_hash: str
    storage_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: UUID
    organization_id: UUID
    workspace_id: UUID | None = None
    title: str
    document_type: str
    language: str
    status: str
    metadata: dict = Field(default_factory=dict)
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
    current_version: DocumentVersionResponse | None = None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class CreateCollectionRequest(BaseModel):
    name: str
    description: str | None = None
    workspace_id: UUID | None = None
    legal_domain_id: str = "iran-oil-gas"


class UpdateCollectionRequest(BaseModel):
    name: str | None = None
    description: str | None = None


class KnowledgeCollectionResponse(BaseModel):
    id: UUID
    organization_id: UUID
    workspace_id: UUID | None = None
    name: str
    description: str | None = None
    legal_domain_id: str | None = None
    document_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AISessionScope(BaseModel):
    document_ids: list[UUID] = Field(default_factory=list)
    collection_ids: list[UUID] = Field(default_factory=list)


class CreateAISessionRequest(BaseModel):
    title: str = "New session"
    workspace_id: UUID | None = None
    legal_domain_id: str = "iran-oil-gas"
    scope: AISessionScope = Field(default_factory=AISessionScope)


class CitationResponse(BaseModel):
    document_id: UUID
    document_title: str | None = None
    chunk_id: UUID | None = None
    excerpt: str
    page_number: int | None = None


class AIMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    citations: list[CitationResponse] = Field(default_factory=list)
    model_version: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AISessionResponse(BaseModel):
    id: UUID
    organization_id: UUID
    workspace_id: UUID | None = None
    title: str
    legal_domain_id: str
    scope: AISessionScope
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AISessionDetailResponse(AISessionResponse):
    messages: list[AIMessageResponse] = Field(default_factory=list)


class SendMessageRequest(BaseModel):
    content: str
    stream: bool = False


class AuditEventResponse(BaseModel):
    id: UUID
    organization_id: UUID
    user_id: UUID | None = None
    user_email: str | None = None
    action: str
    resource_type: str
    resource_id: UUID | None = None
    metadata: dict = Field(default_factory=dict)
    ip_address: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditEventListResponse(BaseModel):
    items: list[AuditEventResponse]
    total: int
    page: int
    page_size: int
