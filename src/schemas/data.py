"""Pydantic schemas for validation and serialization."""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DataRecord(BaseModel):
    """Unified data record schema."""

    source: str
    source_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    url: Optional[str] = None
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PaginatedResponse(BaseModel):
    """Pagination metadata response."""

    request_id: str
    total_count: int
    limit: int
    offset: int
    api_latency_ms: float
    data: list


class HealthStatus(BaseModel):
    """Health check response."""

    status: str
    db_connected: bool
    etl_last_run: Optional[datetime] = None
    etl_status: str = "unknown"


class ETLStats(BaseModel):
    """ETL statistics response."""

    last_run_id: Optional[str] = None
    total_records_processed: int = 0
    total_records_inserted: int = 0
    total_records_failed: int = 0
    last_run_timestamp: Optional[datetime] = None
    last_run_status: Optional[str] = None
    last_failure_timestamp: Optional[datetime] = None
    runs: list = Field(default_factory=list)


class ETLRunMetadata(BaseModel):
    """ETL run metadata."""

    run_id: str
    source: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    records_processed: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_failed: int = 0
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
