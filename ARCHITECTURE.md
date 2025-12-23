# Architecture & Design Document

## System Overview

The Kasparro Backend is a production-grade ETL and API system designed for ingesting data from multiple sources and exposing it through a scalable REST API.

```
┌─────────────────────────────────────────────────────────────┐
│                  Data Sources (External)                      │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│   │ API #1       │    │ CSV Files    │    │ API #2       │  │
│   │ (REST)       │    │ (Local/S3)   │    │ (REST)       │  │
│   └──────────────┘    └──────────────┘    └──────────────┘  │
└────────────┬─────────────────┬───────────────────┬──────────┘
             │                 │                   │
             ▼                 ▼                   ▼
    ┌────────────────────────────────────────────────────┐
    │            ETL Pipeline (src/ingestion/)            │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
    │  │ Fetcher      │─→│ Transformer  │─→│Validator │  │
    │  │ (async)      │  │ (normalize)  │  │(Pydantic)│  │
    │  └──────────────┘  └──────────────┘  └──────────┘  │
    │                                                      │
    │  Error Handling & Checkpoints                       │
    │  ├─ Retry logic (exponential backoff)              │
    │  ├─ Checkpoint tracking (resume capability)        │
    │  ├─ Idempotent writes (no duplicates)             │
    │  └─ Comprehensive error logging                    │
    └──────────────────────┬──────────────────────────────┘
                           │
    ┌──────────────────────▼──────────────────────────────┐
    │        PostgreSQL Database (Data Layer)             │
    │                                                      │
    │  Raw Tables:                                        │
    │  ├─ raw_data_api (API records as-received)        │
    │  ├─ raw_data_csv (CSV records as-received)        │
    │                                                     │
    │  Normalized Tables:                                │
    │  ├─ normalized_data (unified schema)              │
    │                                                     │
    │  Metadata Tables:                                  │
    │  ├─ etl_checkpoint (incremental tracking)         │
    │  └─ etl_run (execution history & stats)          │
    └──────────────────────┬──────────────────────────────┘
                           │
    ┌──────────────────────▼──────────────────────────────┐
    │          FastAPI Application (API Layer)            │
    │  (src/api/main.py)                                  │
    │                                                      │
    │  Endpoints:                                         │
    │  ├─ GET /health           (status check)           │
    │  ├─ GET /data             (paginated data)         │
    │  ├─ GET /stats            (ETL statistics)         │
    │  └─ GET /docs, /redoc     (auto-generated docs)   │
    │                                                      │
    │  Features:                                          │
    │  ├─ Pagination (limit, offset)                     │
    │  ├─ Filtering (source parameter)                   │
    │  ├─ Request tracking (request_id)                  │
    │  ├─ Latency measurement (api_latency_ms)          │
    │  └─ Structured error responses                     │
    └──────────────────────┬──────────────────────────────┘
                           │
    ┌──────────────────────▼──────────────────────────────┐
    │            Clients (External)                       │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
    │  │Web Browser   │  │Mobile App    │  │Backend   │  │
    │  │(REST calls)  │  │(REST calls)  │  │Services  │  │
    │  └──────────────┘  └──────────────┘  └──────────┘  │
    └─────────────────────────────────────────────────────┘
```

## Core Components

### 1. Configuration Layer (`src/core/`)

**Files:**
- `config.py` - Environment-based configuration
- `database.py` - Database connection pooling & session management
- `models.py` - SQLAlchemy ORM models
- `logging_config.py` - Structured logging setup
- `etl_config.py` - ETL source configurations

**Key Features:**
- Externalized configuration (environment variables)
- Connection pooling for efficiency
- Async/await support throughout
- Structured JSON logging for production

### 2. Data Ingestion Layer (`src/ingestion/`)

**Files:**
- `runner.py` - ETL orchestration with retry logic

**Features:**
- Multi-source support (API, CSV)
- Async data fetching
- Error recovery with exponential backoff
- Checkpoint-based resumption

### 3. Service Layer (`src/services/`)

**Files:**
- `ingestion.py` - Core ETL business logic

**DataIngestionService Methods:**
```python
async def ingest_from_api()      # Fetch from REST APIs
async def ingest_from_csv()      # Read CSV files
async def normalize_data()       # Transform to unified schema
async def _get_checkpoint()      # Track progress
async def _update_checkpoint()   # Resume capability
async def create_run()           # Track ETL execution
async def update_run()           # Record final stats
```

### 4. Schema Layer (`src/schemas/`)

**Files:**
- `data.py` - Pydantic models for validation

**Models:**
- `DataRecord` - Unified data schema
- `PaginatedResponse` - API response format
- `HealthStatus` - System status
- `ETLStats` - ETL metrics

### 5. API Layer (`src/api/`)

**Files:**
- `main.py` - FastAPI application & routes
- `routes.py` - Route organization (for future expansion)

**Endpoints:**
1. `GET /health` → System status
2. `GET /data` → Paginated data retrieval
3. `GET /stats` → ETL statistics
4. `GET /docs` → Swagger UI
5. `GET /redoc` → ReDoc documentation

---

## Data Flow

### ETL Process Flow

```
1. FETCH PHASE
   ├─ Retrieve data from source (API/CSV)
   ├─ Check authentication (API key)
   └─ Handle pagination/large files

2. STORE PHASE
   ├─ Validate data structure
   ├─ Check for duplicates (idempotent)
   ├─ Store in raw_data_* tables
   ├─ Commit in batches
   └─ Update checkpoint

3. NORMALIZE PHASE
   ├─ Read raw_data_* tables
   ├─ Map to unified DataRecord schema
   ├─ Apply type validation (Pydantic)
   ├─ Insert/update in normalized_data
   └─ Mark raw records as processed

4. PERSIST PHASE
   ├─ Record run metrics (etl_run table)
   ├─ Track final checkpoint
   ├─ Log execution summary
   └─ Report success/failure

5. MONITORING PHASE
   ├─ Store run metadata
   ├─ Track duration
   ├─ Record error messages
   └─ Enable history queries
```

### API Request Flow

```
Client Request
     │
     ▼
┌─────────────────────┐
│ Route Handler       │
│ (FastAPI)           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Generate request_id │
│ Start timer         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Get DB Session      │
│ (Connection pool)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Execute Query       │
│ (with filters)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Serialize Response  │
│ (Pydantic)          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Calculate latency   │
│ Return response     │
└──────────┬──────────┘
           │
           ▼
Client Response
```

---

## Database Schema

### Raw Data Tables

```sql
-- API raw data (received as-is)
CREATE TABLE raw_data_api (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    raw_data JSONB NOT NULL,
    ingested_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    UNIQUE(source, external_id)
);

-- CSV raw data (received as-is)
CREATE TABLE raw_data_csv (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    raw_data JSONB NOT NULL,
    ingested_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    UNIQUE(source, external_id)
);
```

### Normalized Data Table

```sql
-- Unified schema across all sources
CREATE TABLE normalized_data (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    data JSONB NOT NULL,  -- Full DataRecord as JSON
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source, source_id),
    INDEX(source),
    INDEX(created_at)
);
```

### Metadata Tables

```sql
-- ETL checkpoint for resumption
CREATE TABLE etl_checkpoint (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(50) UNIQUE NOT NULL,
    last_processed_id VARCHAR(255),
    last_processed_timestamp TIMESTAMP,
    checkpoint_timestamp TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'success'
);

-- ETL execution history
CREATE TABLE etl_run (
    id BIGSERIAL PRIMARY KEY,
    run_id VARCHAR(255) UNIQUE NOT NULL,
    source VARCHAR(50) NOT NULL,
    records_processed INT DEFAULT 0,
    records_inserted INT DEFAULT 0,
    records_updated INT DEFAULT 0,
    records_failed INT DEFAULT 0,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_ms INT,
    status VARCHAR(20),  -- 'success', 'failed', 'in_progress'
    error_message TEXT,
    metadata JSONB,
    INDEX(run_id),
    INDEX(source),
    INDEX(start_time)
);
```

---

## Key Design Decisions

### 1. Async/Await Throughout
**Why:** Better performance for I/O-bound operations (API calls, database queries)
```python
async def ingest_from_api():
    # Multiple concurrent API requests
    async with aiohttp.ClientSession() as session:
        data = await session.get(url)
```

### 2. Raw → Normalized Two-Table Approach
**Why:** Preserves original data and enables schema evolution
- Raw tables: Store data exactly as received
- Normalized tables: Apply transformations and unify schema

### 3. Checkpoint-Based Incremental Ingestion
**Why:** Scales to large datasets, avoids reprocessing
```python
checkpoint = await service._get_checkpoint(source)
start_row = int(checkpoint.last_processed_id or 0)
# Process only new records since last_processed_id
```

### 4. Idempotent Writes
**Why:** Safe for retries and distributed systems
```sql
INSERT ... ON CONFLICT (source, source_id) DO UPDATE ...
```

### 5. Pydantic for Schema Validation
**Why:** Type safety + automatic documentation
```python
class DataRecord(BaseModel):
    source: str
    source_id: str
    title: Optional[str] = None
```

### 6. Connection Pooling
**Why:** Efficient database resource usage
```python
AsyncSessionLocal = sessionmaker(async_engine)  # Auto-pools
```

---

## Error Handling & Recovery

### Retry Strategy
```python
async def run_etl_with_backoff(sources, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await run_etl(sources)
        except Exception as e:
            wait_time = 2 ** attempt  # exponential: 1s, 2s, 4s
            await asyncio.sleep(wait_time)
```

### Checkpoint Recovery
- On failure, ETL records last successful position
- On restart, begins from last checkpoint
- Prevents duplicate processing

### Type Validation
- Pydantic validates all incoming data
- Invalid records logged but don't crash ETL
- Failed records tracked in etl_run.records_failed

---

## Performance Considerations

### Batch Operations
```python
ETL_BATCH_SIZE = 100  # Commit every 100 records
ETL_CHECKPOINT_INTERVAL = 100
```

### Connection Pooling
- Default pool_size=20, max_overflow=10
- Pre-ping enabled to detect dead connections

### Indexing
```sql
CREATE INDEX idx_source ON normalized_data(source);
CREATE INDEX idx_created_at ON normalized_data(created_at);
CREATE INDEX idx_run_id ON etl_run(run_id);
```

### Pagination
- Default limit: 10, max: 100
- Offset-based for simplicity

---

## Security

### Authentication
- API keys via environment variables (not hardcoded)
- Stored in .env file (git-ignored)
- Passed securely in request headers

### Database
- Connection pooling prevents resource exhaustion
- Parameterized queries prevent SQL injection
- Non-root user in Docker container

### API
- Input validation (Pydantic)
- Output sanitization
- CORS can be enabled if needed

---

## Monitoring & Observability

### Structured Logging
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "logger": "src.services.ingestion",
  "message": "Completed ingestion for api_source: 100 processed, 95 inserted"
}
```

### Metrics Available
- Records processed/inserted/failed
- ETL run duration
- Last run timestamp
- API response latency

### Health Checks
- Database connectivity
- ETL last-run status
- Container health (Docker)

---

## Testing Strategy

### Unit Tests
- Normalization logic
- Checkpoint management
- Pydantic validation

### Integration Tests
- Full ETL pipeline
- API endpoint responses
- Database operations

### Smoke Tests
- End-to-end data flow
- Error recovery
- Performance baselines

---

## Scalability

### Horizontal Scaling
- Stateless API services (multiple instances)
- Load balancer distributes requests
- Database handles multiple concurrent connections

### Vertical Scaling
- Increase CPU/memory for worker processes
- Larger ETL batch sizes
- Connection pool adjustments

### Data Partitioning
- Shard by source
- Time-based partitions for large tables

---

## Future Enhancements

1. **Schema Drift Detection** - Monitor for unexpected field changes
2. **Rate Limiting** - Per-source rate limits with backoff
3. **Caching Layer** - Redis for frequently accessed data
4. **Search** - Full-text search on normalized_data
5. **Real-time Streaming** - Kafka/RabbitMQ for live data
6. **GraphQL API** - Alternative query interface

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Pydantic v2](https://docs.pydantic.dev/latest/)
- [PostgreSQL JSON Support](https://www.postgresql.org/docs/current/datatype-json.html)

