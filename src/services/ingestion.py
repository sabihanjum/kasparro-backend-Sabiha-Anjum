"""Data ingestion service for handling multiple sources."""
import asyncio
import csv
import io
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import config
from src.core.models import (
    ETLCheckpoint,
    ETLRun,
    NormalizedData,
    RawDataAPI,
    RawDataCSV,
)
from src.schemas.data import DataRecord

logger = logging.getLogger(__name__)


class DataIngestionService:
    """Service for ingesting data from multiple sources."""

    def __init__(self, session: AsyncSession):
        """Initialize ingestion service.
        
        Args:
            session: AsyncSession for database operations
        """
        self.session = session
        self.api_key = config.API_KEY
        self.timeout = aiohttp.ClientTimeout(total=config.API_TIMEOUT_SECONDS)

    async def ingest_from_api(
        self,
        source_name: str,
        api_url: str,
        run_id: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, int, int]:
        """Ingest data from API source.
        
        Args:
            source_name: Name of the API source
            api_url: URL to fetch data from
            run_id: ID of the ETL run
            headers: Optional custom headers
            
        Returns:
            Tuple of (records_processed, records_inserted, records_failed)
        """
        records_processed = 0
        records_inserted = 0
        records_failed = 0

        try:
            # Get checkpoint
            checkpoint = await self._get_checkpoint(source_name)
            
            # Prepare headers with auth
            request_headers = headers or {}
            if self.api_key:
                request_headers["Authorization"] = f"Bearer {self.api_key}"
            request_headers["User-Agent"] = "Kasparro-ETL/1.0"

            # Fetch data
            async with aiohttp.ClientSession(timeout=self.timeout) as client:
                async with client.get(api_url, headers=request_headers) as response:
                    if response.status != 200:
                        raise Exception(
                            f"API returned {response.status}: {await response.text()}"
                        )
                    
                    data = await response.json()
                    
                    # Handle different response formats
                    if isinstance(data, list):
                        # API returns array directly
                        records = data
                    elif isinstance(data, dict):
                        # Handle paginated/wrapped responses
                        records = data.get("results", data.get("data", [data]))
                        if isinstance(records, dict):
                            records = [records]
                    else:
                        records = [data]

                    # Process records
                    for record in records:
                        try:
                            records_processed += 1
                            
                            # Check if record already exists
                            external_id = str(record.get("id", record.get("pk")))
                            existing = await self.session.execute(
                                select(RawDataAPI).where(
                                    and_(
                                        RawDataAPI.source == source_name,
                                        RawDataAPI.external_id == external_id,
                                    )
                                )
                            )
                            
                            if not existing.scalar_one_or_none():
                                # Store raw data
                                raw_data = RawDataAPI(
                                    source=source_name,
                                    external_id=external_id,
                                    raw_data=record,
                                    processed=False,
                                )
                                self.session.add(raw_data)
                                records_inserted += 1
                                
                        except Exception as e:
                            logger.error(f"Error processing API record: {e}")
                            records_failed += 1

                    await self.session.commit()

                    # Update checkpoint
                    await self._update_checkpoint(
                        source_name,
                        last_id=str(records[-1].get("id")) if records else None,
                        status="success"
                    )

        except Exception as e:
            logger.error(f"Error ingesting from API {source_name}: {e}")
            await self._update_checkpoint(source_name, status="failed")
            raise

        return records_processed, records_inserted, records_failed

    async def ingest_from_csv(
        self,
        source_name: str,
        csv_path: str,
        run_id: str,
    ) -> Tuple[int, int, int]:
        """Ingest data from CSV file.
        
        Args:
            source_name: Name of the CSV source
            csv_path: Path to CSV file
            run_id: ID of the ETL run
            
        Returns:
            Tuple of (records_processed, records_inserted, records_failed)
        """
        records_processed = 0
        records_inserted = 0
        records_failed = 0

        try:
            # Get checkpoint
            checkpoint = await self._get_checkpoint(source_name)
            start_row = int(checkpoint.last_processed_id or 0) if checkpoint else 0

            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row_idx, row in enumerate(reader):
                    try:
                        if row_idx < start_row:
                            continue

                        records_processed += 1
                        
                        # Create external ID from row data
                        external_id = row.get("id", f"{source_name}_{row_idx}")
                        
                        # Check if record already exists
                        existing = await self.session.execute(
                            select(RawDataCSV).where(
                                and_(
                                    RawDataCSV.source == source_name,
                                    RawDataCSV.external_id == external_id,
                                )
                            )
                        )
                        
                        if not existing.scalar_one_or_none():
                            # Store raw data
                            raw_data = RawDataCSV(
                                source=source_name,
                                external_id=external_id,
                                raw_data=dict(row),
                                processed=False,
                            )
                            self.session.add(raw_data)
                            records_inserted += 1
                        
                        # Commit in batches
                        if records_processed % config.ETL_BATCH_SIZE == 0:
                            await self.session.commit()
                            await self._update_checkpoint(
                                source_name,
                                last_id=str(row_idx),
                            )

                    except Exception as e:
                        logger.error(f"Error processing CSV row {row_idx}: {e}")
                        records_failed += 1

            await self.session.commit()
            
            # Final checkpoint update
            await self._update_checkpoint(
                source_name,
                last_id=str(row_idx),
                status="success"
            )

        except Exception as e:
            logger.error(f"Error ingesting from CSV {source_name}: {e}")
            await self._update_checkpoint(source_name, status="failed")
            raise

        return records_processed, records_inserted, records_failed

    async def normalize_data(self, run_id: str) -> Tuple[int, int]:
        """Normalize raw data into unified schema.
        
        Args:
            run_id: ID of the ETL run
            
        Returns:
            Tuple of (records_normalized, records_updated)
        """
        records_normalized = 0
        records_updated = 0

        try:
            # Process API raw data
            api_records = await self.session.execute(
                select(RawDataAPI).where(RawDataAPI.processed == False)
            )
            
            for raw_record in api_records.scalars():
                try:
                    normalized = self._normalize_api_record(
                        raw_record.source, raw_record.raw_data
                    )
                    
                    # Check if record exists
                    existing = await self.session.execute(
                        select(NormalizedData).where(
                            and_(
                                NormalizedData.source == raw_record.source,
                                NormalizedData.source_id == raw_record.external_id,
                            )
                        )
                    )
                    
                    existing_record = existing.scalar_one_or_none()
                    if existing_record:
                        existing_record.data = normalized.model_dump(mode='json')
                        records_updated += 1
                    else:
                        normalized_data = NormalizedData(
                            source=raw_record.source,
                            source_id=raw_record.external_id,
                            data=normalized.model_dump(mode='json'),
                        )
                        self.session.add(normalized_data)
                        records_normalized += 1
                    
                    raw_record.processed = True

                except Exception as e:
                    logger.error(f"Error normalizing API record: {e}")

            # Process CSV raw data
            csv_records = await self.session.execute(
                select(RawDataCSV).where(RawDataCSV.processed == False)
            )
            
            for raw_record in csv_records.scalars():
                try:
                    normalized = self._normalize_csv_record(
                        raw_record.source, raw_record.raw_data
                    )
                    
                    # Check if record exists
                    existing = await self.session.execute(
                        select(NormalizedData).where(
                            and_(
                                NormalizedData.source == raw_record.source,
                                NormalizedData.source_id == raw_record.external_id,
                            )
                        )
                    )
                    
                    existing_record = existing.scalar_one_or_none()
                    if existing_record:
                        existing_record.data = normalized.model_dump(mode='json')
                        records_updated += 1
                    else:
                        normalized_data = NormalizedData(
                            source=raw_record.source,
                            source_id=raw_record.external_id,
                            data=normalized.model_dump(mode='json'),
                        )
                        self.session.add(normalized_data)
                        records_normalized += 1
                    
                    raw_record.processed = True

                except Exception as e:
                    logger.error(f"Error normalizing CSV record: {e}")

            await self.session.commit()

        except Exception as e:
            logger.error(f"Error normalizing data: {e}")
            raise

        return records_normalized, records_updated

    def _normalize_api_record(self, source: str, raw_data: Dict[str, Any]) -> DataRecord:
        """Normalize API record to unified schema."""
        # Map common API fields to unified schema
        return DataRecord(
            source=source,
            source_id=str(raw_data.get("id", "")),
            title=raw_data.get("title") or raw_data.get("name"),
            description=raw_data.get("description") or raw_data.get("summary"),
            content=raw_data.get("content") or raw_data.get("body"),
            author=raw_data.get("author") or raw_data.get("creator"),
            published_at=raw_data.get("published_at") or raw_data.get("created_at"),
            url=raw_data.get("url") or raw_data.get("link"),
            category=raw_data.get("category") or raw_data.get("type"),
            metadata=raw_data,
        )

    def _normalize_csv_record(self, source: str, raw_data: Dict[str, str]) -> DataRecord:
        """Normalize CSV record to unified schema."""
        return DataRecord(
            source=source,
            source_id=str(raw_data.get("id", "")),
            title=raw_data.get("title"),
            description=raw_data.get("description"),
            content=raw_data.get("content"),
            author=raw_data.get("author"),
            published_at=raw_data.get("published_at"),
            url=raw_data.get("url"),
            category=raw_data.get("category"),
            metadata=raw_data,
        )

    async def _get_checkpoint(self, source: str) -> Optional[ETLCheckpoint]:
        """Get checkpoint for a source."""
        result = await self.session.execute(
            select(ETLCheckpoint).where(ETLCheckpoint.source == source)
        )
        return result.scalar_one_or_none()

    async def _update_checkpoint(
        self,
        source: str,
        last_id: Optional[str] = None,
        status: str = "in_progress",
    ) -> None:
        """Update or create checkpoint for a source."""
        checkpoint = await self._get_checkpoint(source)
        
        if checkpoint:
            if last_id:
                checkpoint.last_processed_id = last_id
            checkpoint.status = status
            checkpoint.checkpoint_timestamp = datetime.utcnow()
        else:
            checkpoint = ETLCheckpoint(
                source=source,
                last_processed_id=last_id,
                last_processed_timestamp=datetime.utcnow(),
                status=status,
                checkpoint_timestamp=datetime.utcnow(),
            )
            self.session.add(checkpoint)
        
        await self.session.commit()

    async def create_run(
        self,
        source: str,
        status: str = "in_progress"
    ) -> str:
        """Create an ETL run record."""
        run_id = f"run_{source}_{uuid.uuid4().hex[:8]}"
        run = ETLRun(
            run_id=run_id,
            source=source,
            status=status,
            start_time=datetime.utcnow(),
        )
        self.session.add(run)
        await self.session.commit()
        return run_id

    async def update_run(
        self,
        run_id: str,
        processed: int = 0,
        inserted: int = 0,
        updated: int = 0,
        failed: int = 0,
        status: str = "in_progress",
        error_message: Optional[str] = None,
    ) -> None:
        """Update ETL run record."""
        result = await self.session.execute(
            select(ETLRun).where(ETLRun.run_id == run_id)
        )
        run = result.scalar_one_or_none()
        
        if run:
            run.records_processed = processed
            run.records_inserted = inserted
            run.records_updated = updated
            run.records_failed = failed
            run.status = status
            run.error_message = error_message
            
            if status in ["success", "failed"]:
                run.end_time = datetime.utcnow()
                if run.start_time:
                    run.duration_ms = int(
                        (run.end_time - run.start_time).total_seconds() * 1000
                    )
            
            await self.session.commit()
