"""Background task scheduler using APScheduler."""
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.core.etl_config import ETL_SOURCES
from src.ingestion.runner import run_etl_with_backoff

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: AsyncIOScheduler | None = None


async def start_scheduler() -> AsyncIOScheduler:
    """Start the background task scheduler.
    
    Returns:
        AsyncIOScheduler: The scheduler instance
    """
    global _scheduler
    
    if _scheduler is not None:
        logger.warning("Scheduler already running")
        return _scheduler
    
    _scheduler = AsyncIOScheduler()
    
    # Schedule ETL to run every 6 hours (at 0, 6, 12, 18 UTC)
    _scheduler.add_job(
        run_etl_with_backoff,
        CronTrigger(hour="0,6,12,18"),
        args=(ETL_SOURCES,),
        id="etl_schedule_6h",
        name="ETL Pipeline (6-hourly)",
        misfire_grace_time=900,  # 15-minute grace period
        coalesce=True,  # Don't stack missed jobs
        max_instances=1,  # Only one job at a time
    )
    
    _scheduler.start()
    logger.info(f"Scheduler started at {datetime.utcnow().isoformat()}")
    
    return _scheduler


async def stop_scheduler() -> None:
    """Stop the background task scheduler."""
    global _scheduler
    
    if _scheduler is None:
        logger.warning("Scheduler not running")
        return
    
    _scheduler.shutdown(wait=True)
    _scheduler = None
    logger.info(f"Scheduler stopped at {datetime.utcnow().isoformat()}")


def get_scheduler() -> AsyncIOScheduler | None:
    """Get the current scheduler instance.
    
    Returns:
        AsyncIOScheduler | None: The scheduler if running, None otherwise
    """
    return _scheduler
