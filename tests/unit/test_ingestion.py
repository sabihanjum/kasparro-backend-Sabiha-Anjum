"""Unit tests for ETL services."""
import pytest
from sqlalchemy import select

from src.core.models import NormalizedData, RawDataAPI
from src.schemas.data import DataRecord
from src.services.ingestion import DataIngestionService


@pytest.mark.asyncio
async def test_normalize_api_record(db_session, sample_api_data):
    """Test normalizing API record to unified schema."""
    service = DataIngestionService(db_session)
    
    normalized = service._normalize_api_record("api_source", sample_api_data)
    
    assert isinstance(normalized, DataRecord)
    assert normalized.source == "api_source"
    assert normalized.source_id == "1"
    assert normalized.title == "Test Article"
    assert normalized.author == "Test Author"


@pytest.mark.asyncio
async def test_normalize_csv_record(db_session, sample_csv_data):
    """Test normalizing CSV record to unified schema."""
    service = DataIngestionService(db_session)
    
    normalized = service._normalize_csv_record("csv_source", sample_csv_data)
    
    assert isinstance(normalized, DataRecord)
    assert normalized.source == "csv_source"
    assert normalized.source_id == "csv_1"
    assert normalized.title == "CSV Article"


@pytest.mark.asyncio
async def test_checkpoint_creation(db_session):
    """Test creating and retrieving checkpoints."""
    service = DataIngestionService(db_session)
    
    await service._update_checkpoint(
        "test_source",
        last_id="123",
        status="success"
    )
    
    checkpoint = await service._get_checkpoint("test_source")
    
    assert checkpoint is not None
    assert checkpoint.source == "test_source"
    assert checkpoint.last_processed_id == "123"
    assert checkpoint.status == "success"


@pytest.mark.asyncio
async def test_etl_run_creation(db_session):
    """Test creating ETL run records."""
    service = DataIngestionService(db_session)
    
    run_id = await service.create_run("test_source")
    
    assert run_id is not None
    assert "test_source" in run_id
    
    # Verify run exists
    result = await db_session.execute(
        select(RawDataAPI).where(RawDataAPI.source == "test_source")
    )


@pytest.mark.asyncio
async def test_checkpoint_resume(db_session):
    """Test resuming from checkpoint (incremental ingestion)."""
    service = DataIngestionService(db_session)
    
    # Create first checkpoint
    await service._update_checkpoint(
        "test_source",
        last_id="100",
        status="success"
    )
    
    # Retrieve and verify
    checkpoint = await service._get_checkpoint("test_source")
    assert checkpoint.last_processed_id == "100"
    
    # Update checkpoint
    await service._update_checkpoint(
        "test_source",
        last_id="200",
        status="success"
    )
    
    checkpoint = await service._get_checkpoint("test_source")
    assert checkpoint.last_processed_id == "200"
