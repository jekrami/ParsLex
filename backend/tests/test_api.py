"""ParsLex backend tests."""

import os
import sys
from pathlib import Path

# Use in-memory SQLite before any app imports create the Postgres engine
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from apps.api.core.database import Base, get_db
from apps.api.main import app

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def client():
    import apps.api.core.database as db_module
    import apps.api.main as main_module

    original_engine = db_module.engine
    original_local = db_module.SessionLocal

    db_module.engine = engine
    db_module.SessionLocal = TestingSessionLocal
    main_module.SessionLocal = TestingSessionLocal

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    main_module.seed_database()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    db_module.engine = original_engine
    db_module.SessionLocal = original_local
    main_module.SessionLocal = original_local
    Base.metadata.drop_all(bind=engine)
    db.close()


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_login_and_me(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@parslex.com", "password": "admin123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    token = data["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "admin@parslex.com"


def test_list_organizations(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@parslex.com", "password": "admin123"},
    )
    token = login.json()["access_token"]
    res = client.get("/api/v1/organizations", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["total"] >= 1
