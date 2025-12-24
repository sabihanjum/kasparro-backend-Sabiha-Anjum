# Kasparro Backend - Production Improvements (Post-Pass)

## Summary of Changes

Following the PASS evaluation (80/100), this document tracks architectural improvements addressing the evaluation feedback. The main issue (missing entity unification) has now been **fully implemented** (December 24, 2025).

---

## Critical Fix: Entity Unification (Cross-Source Deduplication)

### Status: ✅ IMPLEMENTED (Dec 24, 2025)

### Issue Addressed (Evaluation Feedback - 20 Points Lost)
The evaluation identified that normalization was using only `(source, source_id)` as a unique key. This meant the same entity appearing in multiple sources resulted in duplicate records, failing the architectural requirement for cross-source identity unification.

**Evaluation Quote:**
> "The normalization process is purely a schema mapping (transforming JSON fields to DataRecord fields) rather than an identity resolution process. There is no logic to detect duplicates across sources (e.g., matching by Title or Hash). This results in data silos within the 'normalized' table."

### Solution Implemented
**Hash-based Entity Deduplication with Canonical IDs**

#### Database Schema Changes ([src/core/models.py](src/core/models.py))
Added to `NormalizedData` table:
- `entity_id` (VARCHAR(64)): Canonical entity identifier shared across all sources
- `content_hash` (VARCHAR(64)): SHA-256 hash of normalized title + content for duplicate detection
- `UniqueConstraint` on `(source, source_id)`: Prevents duplicate records from same source
- Indexes on `entity_id` and `content_hash` for query performance

#### Normalization Logic ([src/services/ingestion.py](src/services/ingestion.py))
Implemented three-step duplicate detection:

1. **Content Hashing**
   - Normalizes text (lowercase, whitespace removal)
   - Combines title + first 500 chars of content
   - Generates SHA-256 hash

2. **Cross-Source Duplicate Detection**
   ```python
   # Check for existing entity by content hash
   existing_entity = await session.execute(
       select(NormalizedData).where(
           NormalizedData.content_hash == content_hash
       )
   )
   ```

3. **Entity ID Assignment**
   - New content → New `entity_id` (e.g., `entity_a1b2c3d4e5f6g7h8`)
   - Duplicate content → Use existing `entity_id`
   - Logs cross-source matches for auditing

#### Helper Methods
- `_generate_content_hash(record)`: Creates deterministic hash from normalized content
- `_normalize_text(text)`: Standardizes text for comparison
- `_generate_entity_id(content_hash)`: Creates human-readable entity ID

#### Migration Script
Created [migrations/add_entity_unification.sql](migrations/add_entity_unification.sql):
- Adds new columns with indexes
- Backfills existing records with computed hashes and entity IDs
- Validates migration (reports entity count and duplicates detected)

### Example Behavior
```
Source 1 (API): {"title": "Python Guide", "author": "John", "id": "123"}
Source 2 (CSV): {"title": "Python Guide", "author": "Jane", "id": "456"}

After normalization:
- Record 1: entity_id = "entity_a1b2c3d4", source = "api", source_id = "123"
- Record 2: entity_id = "entity_a1b2c3d4", source = "csv", source_id = "456"

Both records share the same entity_id, enabling cross-source queries and analytics.
```

### Benefits
- **Deduplication**: Same content from different sources is recognized as one entity
- **Traceability**: Each source record is preserved with its own `source_id`
- **Analytics**: Query by `entity_id` to see all sources for an entity
- **Audit Trail**: Cross-source matches are logged

### Migration Required
Before running the updated code, execute the migration:
```bash
# Connect to your database
psql $DATABASE_URL -f migrations/add_entity_unification.sql

# Or via docker-compose
docker-compose exec postgres psql -U postgres -d kasparro -f /migrations/add_entity_unification.sql
```

---

## Security Fix: Removed Hardcoded Password

### Status: ✅ FIXED (Dec 24, 2025)

### Issue Addressed (Evaluation Warning)
The evaluation noted: "DATABASE_URL defaults to postgresql://postgres:password@localhost:5432/kasparro. While this is a fallback for local development and easily overridden by env vars, explicit passwords in code—even defaults—are discouraged."

### Solution Implemented
Fixed `src/core/config.py` to remove the explicit password from the DATABASE_URL default:

**Before**:
```python
DATABASE_URL: "postgresql://postgres:password@localhost:5432/kasparro"
```

**After**:
```python
DATABASE_URL: "postgresql://postgres@localhost:5432/kasparro"
```

Password should be set via environment variables or secured connection strings.

---

## Code Quality: Removed Dead Code

### Status: ✅ CLEANED (Dec 24, 2025)

### Issue Addressed (Evaluation Note)
The evaluation noted: "src/core/batch_processor.py contains robust code for concurrent processing, but it is dead code. It is never imported or used in src/services/ingestion.py or src/ingestion/runner.py."

### Solution Implemented
Removed `src/core/batch_processor.py` entirely. The current sequential processing is adequate for the assignment scope. If concurrent processing becomes a requirement, it can be re-implemented with actual integration into the ingestion pipeline.

---

## Previously Implemented Improvements

### 1. ✅ Docker Multi-Stage Build Optimization

Updated [Dockerfile](Dockerfile) to use a **two-stage build process**:

**Stage 1: Builder**
- Installs `build-essential` and `libpq-dev` (compilation tools)
- Installs Python dependencies into `/build/.local`
- ~600MB intermediate layer

**Stage 2: Runtime**
- Starts from fresh `python:3.11-slim` base
- Only installs runtime dependencies (`postgresql-client`, `curl`, `libpq5`)
- Copies pre-built packages from builder stage
- Non-root user (`appuser`) for security
- Final image: ~300-350MB (50% smaller)

### 2. ✅ Internal ETL Scheduler (APScheduler)

Integrated **APScheduler** for self-contained scheduling:

**New Module**: [src/core/scheduler.py](src/core/scheduler.py)
- `start_scheduler()`: Starts background scheduler at app startup
- `stop_scheduler()`: Gracefully stops scheduler at shutdown
- Cron trigger: **Every 6 hours** (0, 6, 12, 18 UTC)
- Misfire handling: 15-minute grace period, coalesce=True (no stacking)
- Max instances: 1 (prevents concurrent runs)

**Integration**: [src/api/main.py](src/api/main.py)
```python
@app.on_event("startup")
async def startup_event():
    init_db()
    await start_scheduler()  # New

@app.on_event("shutdown")
async def shutdown_event():
    await stop_scheduler()    # New
```

### 3. ✅ Removed Hardcoded Credentials (docker-compose.yml)

Replaced all hardcoded values with environment variables in [docker-compose.yml](docker-compose.yml):

**Before**:
```yaml
POSTGRES_PASSWORD: password
DATABASE_URL: postgresql://postgres:password@postgres:5432/kasparro
```

**After**:
```yaml
POSTGRES_USER: ${DB_USER:-postgres}
POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
POSTGRES_DB: ${DB_NAME:-kasparro}
DATABASE_URL: postgresql://${DB_USER:-postgres}:${DB_PASSWORD:-postgres}@postgres:5432/${DB_NAME:-kasparro}
```

### 4. ✅ Orphaned Record Handling (Soft Deletes)

Added soft-delete support to [src/core/models.py](src/core/models.py):

```python
class NormalizedData(Base):
    # ... existing fields ...
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
```

---

## Files Modified

### December 24, 2025 Updates (Evaluation Fixes)
- ✅ `src/core/models.py` — Added entity_id, content_hash, indexes, unique constraints
- ✅ `src/services/ingestion.py` — Implemented cross-source duplicate detection with hash-based entity unification
- ✅ `src/core/config.py` — Removed hardcoded password from DATABASE_URL default
- ✅ `migrations/add_entity_unification.sql` — **New: Database migration script**
- ❌ `src/core/batch_processor.py` — **Removed: Dead code**

### Previous Updates
- ✅ `Dockerfile` — Multi-stage build
- ✅ `docker-compose.yml` — Environment variables
- ✅ `requirements.txt` — Added APScheduler
- ✅ `src/api/main.py` — Scheduler integration
- ✅ `src/core/models.py` — Soft-delete columns
- ✅ `src/core/scheduler.py` — **New: APScheduler module**

---

## Testing & Validation

### Test Updates Required
```bash
# Install dependencies
pip install -r requirements.txt

# Run migration
psql $DATABASE_URL -f migrations/add_entity_unification.sql

# Run full test suite
pytest tests/ -v --cov=src

# Verify scheduler starts cleanly
python -m uvicorn src.api.main:app --reload
```

### Expected Results
- All existing tests still pass
- Entity unification detects cross-source duplicates
- Migration successfully backfills existing data
- No hardcoded credentials in code

---

## Deployment Steps

### Local Testing
```bash
# Update requirements
pip install -r requirements.txt

# Create .env with your values
cp .env.example .env

# Run migration
docker-compose exec postgres psql -U postgres -d kasparro -f /migrations/add_entity_unification.sql

# Rebuild Docker image
docker build -t saba067/kasparro-backend:v3-entity-unification .

# Test locally with docker-compose
docker-compose up
```

### Production Deployment
1. Rebuild image with updated code
2. Push to Docker Hub: `docker push saba067/kasparro-backend:v3-entity-unification`
3. Run migration on production database
4. Update cloud deployment with new image tag
5. Verify entity unification in logs and database

---

## Summary

**Critical Issue Fixed**: Entity unification is now fully implemented with hash-based cross-source duplicate detection.

All improvement areas status:
1. ✅ Docker optimization complete
2. ✅ Internal scheduler implemented
3. ✅ Credentials secured (enhanced Dec 24)
4. ❌ Batch processor removed (dead code)
5. ✅ **Entity unification implemented** (Dec 24) - **Addresses 20-point deduction**
6. ✅ Soft-delete infrastructure in place

**Status**: Core architectural issue resolved. System now implements true cross-source entity unification as required by the evaluation criteria.

---

## Next Steps for Further Improvement

1. **Advanced Entity Matching**
   - Implement fuzzy matching for similar (but not identical) content
   - Add confidence scores for entity matches
   - Build UI dashboard for reviewing entity clusters

2. **Performance Optimization**
   - Re-implement concurrent processing with actual integration
   - Add batch operations to reduce database round-trips
   - Target: 1000+ records/second throughput

3. **Enhanced Orphan Detection**
   - Automated sync detection on each ETL run
   - Configurable retention periods
   - Audit log of deletions

4. **Observability**
   - Add Prometheus metrics for entity unification
   - Track duplicate detection rates
   - Monitor content hash collisions
