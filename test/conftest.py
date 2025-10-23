import pytest
import asyncio
import tempfile
import os
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from main import app
from core.database import Base, get_async_db
from repositories.property import PropertyRepository


pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a temporary test database for each test"""
    # Create temporary database file
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()

    # Create async engine
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{temp_db.name}",
        echo=False,
        future=True
    )

    # Create session factory
    TestSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

    # Cleanup
    await engine.dispose()
    os.unlink(temp_db.name)


@pytest.fixture
async def property_repo(test_db: AsyncSession):
    """Create PropertyRepository instance with test database"""
    return PropertyRepository(test_db)


@pytest.fixture(scope="function")
async def async_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing endpoints"""

    async def override_get_async_db():
        """Override the database dependency"""
        yield test_db

    # Override the dependency
    app.dependency_overrides[get_async_db] = override_get_async_db

    # Create async client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clear overrides
    app.dependency_overrides.clear()