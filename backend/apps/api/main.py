from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.core.config import settings
from apps.api.core.database import Base, SessionLocal, engine
from apps.api.core.security import get_password_hash
from apps.api.models.entities import Membership, Organization, User, Workspace
from apps.api.routers import assistant, audit, auth, collections, documents, organizations
from apps.api.services.storage import storage_service


def seed_database() -> None:
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == settings.default_admin_email).first():
            return

        user = User(
            email=settings.default_admin_email,
            full_name=settings.default_admin_name,
            hashed_password=get_password_hash(settings.default_admin_password),
            role="admin",
        )
        db.add(user)
        db.flush()

        org = Organization(name="Demo Oil & Gas Corp", slug="demo-oil-gas")
        db.add(org)
        db.flush()

        db.add(Membership(user_id=user.id, organization_id=org.id, role="admin"))
        db.add(
            Workspace(
                organization_id=org.id,
                name="Iranian Petroleum Contracts",
                legal_domain_id="iran-oil-gas",
            )
        )
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = settings.api_prefix
app.include_router(auth.router, prefix=api_prefix)
app.include_router(organizations.router, prefix=api_prefix)
app.include_router(documents.router, prefix=api_prefix)
app.include_router(collections.router, prefix=api_prefix)
app.include_router(assistant.router, prefix=api_prefix)
app.include_router(audit.router, prefix=api_prefix)


@app.get("/health")
def health() -> dict:
    from apps.api.services.llm import get_llm_client

    llm_status = get_llm_client().health()
    return {
        "status": "ok",
        "version": settings.app_version,
        "ai": llm_status,
    }
