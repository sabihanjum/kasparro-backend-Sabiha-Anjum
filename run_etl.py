"""Script to run ETL manually or scheduled."""
import asyncio
import logging
from datetime import datetime

from src.core.logging_config import setup_logging
from src.core.etl_config import ETL_SOURCES
from src.ingestion.runner import run_etl_with_backoff

# Setup logging
logger = setup_logging()


async def main():
    """Main ETL execution."""
    logger.info("=" * 60)
    logger.info("Starting Kasparro ETL Pipeline")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    logger.info("=" * 60)
    
    try:
        result = await run_etl_with_backoff(ETL_SOURCES, max_retries=3)
        
        logger.info("=" * 60)
        logger.info("ETL Pipeline Completed Successfully")
        logger.info(f"Total Processed: {result.get('total_processed', 0)}")
        logger.info(f"Total Inserted: {result.get('total_inserted', 0)}")
        logger.info(f"Total Failed: {result.get('total_failed', 0)}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"ETL Pipeline Failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
