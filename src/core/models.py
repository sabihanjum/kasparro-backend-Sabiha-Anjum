"""SQLAlchemy models for the application."""
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class RawDataAPI(Base):
    """Raw data from API sources."""

    __tablename__ = "raw_data_api"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    processed: Mapped[bool] = mapped_column(default=False, index=True)


class RawDataCSV(Base):
    """Raw data from CSV sources."""

    __tablename__ = "raw_data_csv"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    processed: Mapped[bool] = mapped_column(default=False, index=True)


class NormalizedData(Base):
    """Normalized and unified data across all sources."""

    __tablename__ = "normalized_data"
    __table_args__ = (
        UniqueConstraint('source', 'source_id', name='uix_source_source_id'),
        Index('ix_normalized_data_entity_id', 'entity_id'),
        Index('ix_normalized_data_content_hash', 'content_hash'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Canonical entity ID for cross-source unification
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # Content hash for duplicate detection
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    # Soft delete support
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class ETLCheckpoint(Base):
    """ETL run checkpoints for incremental ingestion."""

    __tablename__ = "etl_checkpoint"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    last_processed_id: Mapped[str] = mapped_column(String(255), nullable=True)
    last_processed_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    checkpoint_timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    status: Mapped[str] = mapped_column(String(20), default="success")


class ETLRun(Base):
    """ETL run metadata and statistics."""

    __tablename__ = "etl_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(50), index=True)
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)
    start_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20))  # success, failed, in_progress
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    run_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

