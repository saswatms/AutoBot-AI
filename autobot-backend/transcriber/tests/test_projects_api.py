# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from transcriber.routes.projects import router
from transcriber.database import Database
from transcriber.deps import get_db


@pytest_asyncio.fixture
async def app(tmp_path):
    a = FastAPI()
    db = Database(str(tmp_path / "test.db"))
    await db.connect()

    async def override_db():
        return db

    a.dependency_overrides[get_db] = override_db
    a.include_router(router, prefix="/api/transcriber")

    yield a

    await db.close()


@pytest.mark.asyncio
async def test_create_project(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/api/transcriber/projects", json={"name": "My Project", "description": "desc"})
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "My Project"
        assert "id" in data


@pytest.mark.asyncio
async def test_list_projects(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/transcriber/projects", json={"name": "P1", "description": ""})
        r = await c.get("/api/transcriber/projects")
        assert r.status_code == 200
        assert len(r.json()) >= 1


@pytest.mark.asyncio
async def test_delete_project(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/api/transcriber/projects", json={"name": "P", "description": ""})
        pid = r.json()["id"]
        r2 = await c.delete(f"/api/transcriber/projects/{pid}")
        assert r2.status_code == 204
        r3 = await c.get(f"/api/transcriber/projects/{pid}")
        assert r3.status_code == 404
