"""FastAPI application and routes."""
import logging
import time
import uuid
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.routes import router
from src.core.database import get_db, check_db_connection, init_db
from src.core.logging_config import setup_logging
from src.core.models import ETLRun, NormalizedData
from src.schemas.data import HealthStatus, PaginatedResponse, ETLStats
from src.core.etl_config import ETL_SOURCES
from src.ingestion.runner import run_etl_with_backoff
from src.core.scheduler import start_scheduler, stop_scheduler

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Kasparro Backend",
    description="Production-grade data ingestion and API system",
    version="1.0.0",
)

# Include routes
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and scheduler on startup."""
    try:
        init_db()
        logger.info("Database initialized")
        
        # Start internal scheduler for autonomous ETL
        await start_scheduler()
        logger.info("Internal ETL scheduler started")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully shutdown scheduler."""
    try:
        await stop_scheduler()
        logger.info("Scheduler shutdown complete")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


@app.get("/health", response_model=HealthStatus)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthStatus:
    """Health check endpoint."""
    request_start = time.time()
    
    # Check database connectivity
    db_connected = await check_db_connection()
    
    # Get last ETL run
    result = await db.execute(
        select(ETLRun).order_by(desc(ETLRun.start_time)).limit(1)
    )
    last_run = result.scalar_one_or_none()
    
    return HealthStatus(
        status="healthy" if db_connected else "unhealthy",
        db_connected=db_connected,
        etl_last_run=last_run.end_time if last_run else None,
        etl_status=last_run.status if last_run else "unknown",
    )


@app.get("/data", response_model=PaginatedResponse)
async def get_data(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    source: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    """Get normalized data with pagination and filtering."""
    request_id = str(uuid.uuid4())
    request_start = time.time()
    
    try:
        # Build query
        query = select(NormalizedData)
        
        if source:
            query = query.where(NormalizedData.source == source)
        
        # Get total count
        count_result = await db.execute(
            select(NormalizedData) if not source
            else select(NormalizedData).where(NormalizedData.source == source)
        )
        total_count = len(count_result.all())
        
        # Get paginated results
        results = await db.execute(
            query.offset(offset).limit(limit)
        )
        records = results.scalars().all()
        
        data = [
            {
                "id": record.id,
                "source": record.source,
                "source_id": record.source_id,
                **record.data,
            }
            for record in records
        ]
        
        latency_ms = (time.time() - request_start) * 1000
        
        return PaginatedResponse(
            request_id=request_id,
            total_count=total_count,
            limit=limit,
            offset=offset,
            api_latency_ms=round(latency_ms, 2),
            data=data,
        )
        
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=ETLStats)
async def get_etl_stats(
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> ETLStats:
    """Get ETL statistics and recent run history."""
    try:
        # Get recent runs
        result = await db.execute(
            select(ETLRun).order_by(desc(ETLRun.start_time)).limit(limit)
        )
        runs = result.scalars().all()
        
        # Calculate totals
        total_processed = sum(run.records_processed for run in runs)
        total_inserted = sum(run.records_inserted for run in runs)
        total_failed = sum(run.records_failed for run in runs)
        
        # Get last run details
        last_run = runs[0] if runs else None
        last_failure = next(
            (run for run in runs if run.status == "failed"), None
        )
        
        return ETLStats(
            last_run_id=last_run.run_id if last_run else None,
            total_records_processed=total_processed,
            total_records_inserted=total_inserted,
            total_records_failed=total_failed,
            last_run_timestamp=last_run.end_time if last_run else None,
            last_run_status=last_run.status if last_run else None,
            last_failure_timestamp=last_failure.end_time if last_failure else None,
            runs=[
                {
                    "run_id": run.run_id,
                    "source": run.source,
                    "start_time": run.start_time.isoformat(),
                    "end_time": run.end_time.isoformat() if run.end_time else None,
                    "status": run.status,
                    "records_processed": run.records_processed,
                    "records_inserted": run.records_inserted,
                    "records_updated": run.records_updated,
                    "records_failed": run.records_failed,
                    "duration_ms": run.duration_ms,
                }
                for run in runs
            ],
        )
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.api_route("/etl/run", methods=["GET", "POST"])
async def trigger_etl(background_tasks: BackgroundTasks):
    """Trigger ETL asynchronously and return immediately.

    Useful for manual runs and for Render Cron HTTP jobs.
    """
    try:
        background_tasks.add_task(run_etl_with_backoff, ETL_SOURCES)
        return {"status": "accepted"}
    except Exception as e:
        logger.error(f"Failed to enqueue ETL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
