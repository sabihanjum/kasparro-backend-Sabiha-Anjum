"""ETL runner for orchestrating data ingestion."""
import asyncio
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal
from src.services.ingestion import DataIngestionService

logger = logging.getLogger(__name__)


async def run_etl(
    sources: dict,
) -> dict:
    """Run complete ETL pipeline.
    
    Args:
        sources: Dictionary with source configurations
        
    Returns:
        Dictionary with ETL execution summary
    """
    async with AsyncSessionLocal() as session:
        service = DataIngestionService(session)
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "sources": {},
            "total_processed": 0,
            "total_inserted": 0,
            "total_failed": 0,
        }

        for source_name, config in sources.items():
            logger.info(f"Starting ingestion for source: {source_name}")
            
            try:
                # Create run record
                run_id = await service.create_run(source_name)
                
                # Process based on source type
                if config["type"] == "api":
                    processed, inserted, failed = await service.ingest_from_api(
                        source_name,
                        config["url"],
                        run_id,
                        config.get("headers"),
                    )
                elif config["type"] == "csv":
                    processed, inserted, failed = await service.ingest_from_csv(
                        source_name,
                        config["path"],
                        run_id,
                    )
                else:
                    logger.warning(f"Unknown source type for {source_name}")
                    continue

                # Normalize data
                normalized, updated = await service.normalize_data(run_id)

                # Update run with final stats
                total_records = processed + normalized
                await service.update_run(
                    run_id,
                    processed=processed,
                    inserted=inserted,
                    updated=updated,
                    failed=failed,
                    status="success",
                )

                summary["sources"][source_name] = {
                    "run_id": run_id,
                    "records_processed": processed,
                    "records_inserted": inserted,
                    "records_updated": updated,
                    "records_failed": failed,
                    "records_normalized": normalized,
                    "status": "success",
                }

                summary["total_processed"] += processed
                summary["total_inserted"] += inserted
                summary["total_failed"] += failed

                logger.info(
                    f"Completed ingestion for {source_name}: "
                    f"{processed} processed, {inserted} inserted, "
                    f"{normalized} normalized"
                )

            except Exception as e:
                logger.error(f"Error processing {source_name}: {e}")
                summary["sources"][source_name] = {
                    "status": "failed",
                    "error": str(e),
                }
                summary["total_failed"] += 1

        logger.info(f"ETL pipeline completed: {summary}")
        return summary


async def run_etl_with_backoff(
    sources: dict,
    max_retries: int = 3,
) -> dict:
    """Run ETL with retry logic.
    
    Args:
        sources: Dictionary with source configurations
        max_retries: Maximum number of retries
        
    Returns:
        Dictionary with ETL execution summary
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"ETL attempt {attempt + 1}/{max_retries}")
            return await run_etl(sources)
        except Exception as e:
            logger.error(f"ETL attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.error("All ETL attempts failed")
                raise

    return {}


if __name__ == "__main__":
    # Example configuration
    sources = {
        "api_source": {
            "type": "api",
            "url": "https://api.example.com/data",
        },
        "csv_source": {
            "type": "csv",
            "path": "data/sample.csv",
        },
    }

    asyncio.run(run_etl_with_backoff(sources))
