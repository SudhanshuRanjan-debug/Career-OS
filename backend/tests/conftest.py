"""
Pytest configuration and shared test fixtures using FastAPI TestClient.
Includes in-memory SQLite database setup for authentication, profile, resume, and document testing.
"""

import asyncio
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.core.dependencies import get_storage
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app
import app.models as _app_models  # Ensure all 31 models are loaded
from app.storage.local_storage import LocalStorageBackend



import json
import shutil

# Compile PostgreSQL dialect types for in-memory SQLite test database
@compiles(ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    return "JSON"


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


_orig_array_bind = ARRAY.bind_processor
def _sqlite_array_bind(self, dialect):
    if dialect.name == "sqlite":
        return lambda value: json.dumps(value) if value is not None else None
    return _orig_array_bind(self, dialect)

ARRAY.bind_processor = _sqlite_array_bind

_orig_array_res = ARRAY.result_processor
def _sqlite_array_res(self, dialect, coltype):
    if dialect.name == "sqlite":
        return lambda value: json.loads(value) if isinstance(value, str) else value
    return _orig_array_res(self, dialect, coltype)

ARRAY.result_processor = _sqlite_array_res

_orig_jsonb_bind = JSONB.bind_processor
def _sqlite_jsonb_bind(self, dialect):
    if dialect.name == "sqlite":
        return lambda value: json.dumps(value) if value is not None else None
    return _orig_jsonb_bind(self, dialect)

JSONB.bind_processor = _sqlite_jsonb_bind

_orig_jsonb_res = JSONB.result_processor
def _sqlite_jsonb_res(self, dialect, coltype):
    if dialect.name == "sqlite":
        return lambda value: json.loads(value) if isinstance(value, str) else value
    return _orig_jsonb_res(self, dialect, coltype)

JSONB.result_processor = _sqlite_jsonb_res


@pytest.fixture
def client():
    """Synchronous test client using FastAPI TestClient without DB overrides."""
    with TestClient(fastapi_app) as test_client:
        yield test_client


@pytest.fixture
def test_storage():
    """Isolated temporary storage backend for tests (Windows-safe)."""
    temp_dir = tempfile.mkdtemp()
    backend = LocalStorageBackend(base_path=temp_dir)
    yield backend
    shutil.rmtree(temp_dir, ignore_errors=True)



@pytest.fixture
def db_client(test_storage):
    """
    Test client backed by an isolated in-memory database with all tables created.
    Automatically initializes schema and cleans up dependency overrides.
    """
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def init_schema():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(init_schema())

    async def override_get_db():
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    def override_get_storage():
        return test_storage

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_storage] = override_get_storage

    with TestClient(fastapi_app) as test_client:
        yield test_client

    fastapi_app.dependency_overrides.pop(get_db, None)
    fastapi_app.dependency_overrides.pop(get_storage, None)
    asyncio.run(test_engine.dispose())
