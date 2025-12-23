"""Test configuration and fixtures."""
import asyncio
import os
from typing import Generator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import Base
from src.core.models import ETLRun, NormalizedData, RawDataAPI, RawDataCSV


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_engine():
    """Create test database engine."""
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(test_db_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncSession:
    """Create test database session."""
    TestingSessionLocal = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sample_api_data():
    """Sample API response data."""
    return {
        "id": 1,
        "title": "Test Article",
        "description": "Test Description",
        "content": "Test content body",
        "author": "Test Author",
        "published_at": "2024-01-01T00:00:00",
        "url": "https://example.com/article",
        "category": "test",
    }


@pytest.fixture
def sample_csv_data():
    """Sample CSV row data."""
    return {
        "id": "csv_1",
        "title": "CSV Article",
        "description": "CSV Description",
        "content": "CSV content",
        "author": "CSV Author",
        "published_at": "2024-01-01",
        "url": "https://example.com/csv",
        "category": "csv",
    }
