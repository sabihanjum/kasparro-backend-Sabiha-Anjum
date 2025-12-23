"""Batch processing utilities for concurrent operations."""
import asyncio
import logging
from typing import Any, Callable, List, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def batch_process(
    items: List[T],
    process_fn: Callable[[T], Any],
    batch_size: int = 100,
    max_concurrent: int = 10,
) -> tuple[int, int]:
    """Process items in batches with concurrency control.
    
    Args:
        items: List of items to process
        process_fn: Async function to process each item
        batch_size: Number of items per batch for DB operations
        max_concurrent: Maximum concurrent tasks
        
    Returns:
        Tuple of (processed_count, failed_count)
    """
    processed = 0
    failed = 0
    
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        
        # Process batch with concurrency limit
        tasks = [process_fn(item) for item in batch]
        
        try:
            results = await asyncio.gather(
                *tasks,
                return_exceptions=True
            )
            
            for result in results:
                if isinstance(result, Exception):
                    failed += 1
                    logger.error(f"Batch processing error: {result}")
                else:
                    processed += 1
                    
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            failed += len(batch)
    
    return processed, failed


async def batch_execute_concurrent(
    operations: List[Callable[[], Any]],
    max_concurrent: int = 10,
) -> tuple[int, int]:
    """Execute operations concurrently with a limit.
    
    Args:
        operations: List of async callables to execute
        max_concurrent: Maximum concurrent tasks
        
    Returns:
        Tuple of (successful_count, failed_count)
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_operation(op: Callable[[], Any]) -> bool:
        async with semaphore:
            try:
                await op()
                return True
            except Exception as e:
                logger.error(f"Operation failed: {e}")
                return False
    
    results = await asyncio.gather(
        *[bounded_operation(op) for op in operations],
        return_exceptions=False
    )
    
    success_count = sum(1 for r in results if r)
    failed_count = len(results) - success_count
    
    return success_count, failed_count
