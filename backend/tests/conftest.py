import os
import sys
import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import delete, or_, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app as fastapi_app
from app.db.postgres import Base, get_db
from app.db.neo4j import neo4j_manager, get_neo4j
from app.models.postgres.organization import Organization
from app.models.postgres.domain import Domain
from app.models.postgres.ip import IP
from app.models.postgres.relationship import Relationship
import app.models.postgres as _postgres_models  # noqa: F401


DEFAULT_TEST_DB_URL = (
    "postgresql+asyncpg://postgres:externalhound_pg_pass@localhost:5432/"
    "externalhound_test"
)


def _get_test_database_url() -> str:
    return (
        os.getenv("TEST_DATABASE_URL")
        or os.getenv("EXTERNALHOUND_TEST_DATABASE_URL")
        or DEFAULT_TEST_DB_URL
    )


def _ensure_test_database_name(url: str) -> None:
    database = make_url(url).database
    if not database or "test" not in database.lower():
        raise RuntimeError(
            f"Refusing to run tests against non-test database: {database}"
        )


async def _ensure_test_database(url: str) -> None:
    parsed = make_url(url)
    admin_url = parsed.set(database="postgres")
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": parsed.database},
            )
            exists = result.scalar() is not None
            if not exists:
                await conn.execute(
                    text(f'CREATE DATABASE "{parsed.database}"')
                )
    finally:
        await engine.dispose()


@pytest.fixture
async def test_engine():
    test_db_url = _get_test_database_url()
    _ensure_test_database_name(test_db_url)
    await _ensure_test_database(test_db_url)

    engine = create_async_engine(test_db_url, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest.fixture
def session_factory(test_engine):
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
async def neo4j():
    await neo4j_manager.connect()
    try:
        yield neo4j_manager
    finally:
        await neo4j_manager.close()


@pytest.fixture
def test_prefix() -> str:
    return f"test-{uuid.uuid4().hex}"


@pytest.fixture(autouse=True)
async def cleanup_test_data(session_factory, neo4j, test_prefix):
    yield
    prefix = f"{test_prefix}:"
    async with session_factory() as session:
        await session.execute(
            delete(Relationship).where(
                or_(
                    Relationship.source_external_id.like(f"{prefix}%"),
                    Relationship.target_external_id.like(f"{prefix}%"),
                )
            )
        )
        await session.execute(
            delete(IP).where(IP.external_id.like(f"{prefix}%"))
        )
        await session.execute(
            delete(Domain).where(Domain.external_id.like(f"{prefix}%"))
        )
        await session.execute(
            delete(Organization).where(Organization.external_id.like(f"{prefix}%"))
        )
        await session.commit()

    await neo4j.execute_query(
        "MATCH (n) WHERE n.id STARTS WITH $prefix DETACH DELETE n",
        {"prefix": prefix},
    )


@pytest.fixture
async def async_client(session_factory, neo4j):
    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def override_get_neo4j():
        return neo4j

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_neo4j] = override_get_neo4j

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    fastapi_app.dependency_overrides.clear()
