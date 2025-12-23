# Kasparro Backend - Production Data Ingestion System

A production-grade backend system for ingesting data from multiple sources (APIs, CSV files) with incremental processing, comprehensive API endpoints, and cloud deployment support.

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  External Data Sources                   │
│        (APIs, CSV files, RSS feeds, databases)           │
└────────────────┬────────────────────────────────────────┘
                 │
         ┌───────▼────────┐
         │   ETL Service  │
         │  (Ingestion)   │
         └───────┬────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
    ┌────────┐      ┌──────────┐
    │ Raw    │      │Normalized│
    │ Tables │──────│ Tables   │
    └────────┘      └──────────┘
        │                 │
        └────────┬────────┘
                 ▼
          ┌─────────────┐
          │  PostgreSQL │
          │  Database   │
          └──────┬──────┘
                 ▼
          ┌─────────────┐
          │ FastAPI App │
          │ (GET/POST)  │
          └──────┬──────┘
                 ▼
          ┌─────────────┐
          │   Clients   │
          └─────────────┘
```

## ✅ Tier Completion Status

### P0 - Foundation (REQUIRED) ✓
- [x] P0.1 - Data Ingestion (API + CSV sources)
- [x] P0.2 - Backend API Service (/data, /health)
- [x] P0.3 - Dockerized System (Docker, compose, Makefile)
- [x] P0.4 - Basic Test Suite

### P1 - Growth Layer (REQUIRED) 🚀
- [ ] P1.1 - Third Data Source (RSS/API)
- [ ] P1.2 - Checkpoint & Recovery Logic
- [ ] P1.3 - /stats Endpoint
- [ ] P1.4 - Comprehensive Tests
- [ ] P1.5 - Clean Architecture (✓ Already implemented)

### P2 - Differentiator (OPTIONAL) 🌟
- [ ] P2.1 - Schema Drift Detection
- [ ] P2.2 - Failure Injection + Recovery
- [ ] P2.3 - Rate Limiting + Backoff
- [ ] P2.4 - Observability Layer
- [ ] P2.5 - DevOps Enhancements
- [ ] P2.6 - Run Comparison / Anomaly Detection

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ (if running without Docker)

### Running with Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/kasparro-backend-yourname
cd kasparro-backend-yourname

# Start services
make up

# Services will be available at:
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Database: localhost:5432
```

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add your API_KEY

# Start PostgreSQL (ensure it's running)
# Then run the application
python -m uvicorn src.api.main:app --reload

# Run tests
make test
```

## 📊 Available Endpoints

### Health & Status
```
GET /health
Returns: Database connectivity and last ETL run status

GET /stats
Returns: ETL statistics, recent runs, processing metadata
```

### Data Access
```
GET /data?limit=10&offset=0&source=optional_source
Query Parameters:
  - limit (1-100): Number of records
  - offset (0+): Pagination offset
  - source: Filter by source (optional)

Returns: Paginated results with request_id and api_latency_ms
```

### Interactive API Documentation
```
GET /docs    # Swagger UI
GET /redoc   # ReDoc
```

## 🔧 Configuration

### Environment Variables (.env)
```
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/kasparro

# API Authentication
API_KEY=your-api-key-here

# ETL Configuration
ETL_BATCH_SIZE=100
ETL_CHECKPOINT_INTERVAL=100

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

## 🗄️ Database Schema

### Raw Data Tables
- `raw_data_api` - Raw ingested API records
- `raw_data_csv` - Raw ingested CSV records

### Processed Data Tables
- `normalized_data` - Unified schema across all sources
- `etl_checkpoint` - Tracks ingestion progress (incremental)
- `etl_run` - Metadata for each ETL execution

## 📁 Project Structure

```
kasparro-backend/
├── src/
│   ├── api/
│   │   ├── main.py          # FastAPI application & endpoints
│   │   └── routes.py        # Route definitions
│   ├── core/
│   │   ├── config.py        # Configuration management
│   │   ├── database.py      # Database setup
│   │   ├── logging_config.py# Logging configuration
│   │   └── models.py        # SQLAlchemy ORM models
│   ├── ingestion/
│   │   ├── runner.py        # ETL orchestration
│   │   └── __init__.py
│   ├── services/
│   │   ├── ingestion.py     # Data ingestion service
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── data.py          # Pydantic validation schemas
│   │   └── __init__.py
│   └── __init__.py
├── tests/
│   ├── unit/
│   │   ├── test_api.py      # API endpoint tests
│   │   └── test_ingestion.py# ETL service tests
│   ├── integration/
│   │   └── test_e2e.py      # End-to-end tests
│   └── conftest.py          # Test fixtures
├── data/
│   └── sample.csv           # Sample CSV for testing
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Multi-container setup
├── Makefile                 # Development commands
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
└── README.md               # This file
```

## 🧪 Testing

### Run All Tests
```bash
make test
```

### Run Unit Tests Only
```bash
make test-unit
```

### Run Integration Tests
```bash
make test-integration
```

### Test Coverage
```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

## 🔄 ETL Pipeline

### Ingestion Flow
1. **Fetch** - Get data from API/CSV sources
2. **Store** - Save raw data to `raw_data_*` tables
3. **Normalize** - Transform to unified schema
4. **Checkpoint** - Track processing progress
5. **Validate** - Type checking with Pydantic

### Key Features
- **Incremental Processing**: Only processes new records via checkpoints
- **Idempotent Writes**: Prevents duplicates
- **Error Recovery**: Resumes from last checkpoint on failure
- **Batch Operations**: Commits in configurable batches
- **Secure Authentication**: Handles API keys securely (via env vars)

### Running ETL Manually
```python
import asyncio
from src.ingestion.runner import run_etl_with_backoff

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

result = asyncio.run(run_etl_with_backoff(sources))
print(result)
```

## 🛠️ Makefile Commands

```bash
make up               # Start all containers
make down             # Stop containers
make restart          # Restart containers
make logs             # View backend logs
make logs-db          # View database logs
make test             # Run all tests with coverage
make test-unit        # Run unit tests only
make test-integration # Run integration tests
make clean            # Clean up containers, volumes
make migrate          # Run database migrations
make shell            # Access backend container shell
make psql             # Connect to PostgreSQL
make lint             # Check code quality
make format           # Format code (black, isort)
make type-check       # Type checking with mypy
```

## 📈 Monitoring & Logging

### Logs
- Console output (structured JSON in production)
- Database query logs (in debug mode)
- ETL execution logs with timestamps

### Metrics Available via /stats
- Total records processed
- Records inserted/updated
- Processing failures
- Last run status and duration
- Historical run data

## 🚀 Cloud Deployment

### AWS Deployment
```bash
# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag kasparro-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/kasparro:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/kasparro:latest

# Deploy with ECS/Fargate
# (See AWS documentation for detailed steps)

# Schedule ETL with EventBridge
# (Create cron rule pointing to Lambda/ECS task)
```

### GCP Deployment
```bash
# Push to Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev
docker tag kasparro-backend:latest us-central1-docker.pkg.dev/PROJECT_ID/repo/kasparro:latest
docker push us-central1-docker.pkg.dev/PROJECT_ID/repo/kasparro:latest

# Deploy with Cloud Run
gcloud run deploy kasparro-backend \
  --image us-central1-docker.pkg.dev/PROJECT_ID/repo/kasparro:latest \
  --platform managed
```

## 🔐 Security Best Practices

✅ **Implemented**
- API keys loaded from environment variables (never hardcoded)
- Non-root user in Docker container
- Health checks for container orchestration
- Connection pooling for database safety
- SQL injection prevention via ORM

✅ **Recommended for Production**
- Use secret management (AWS Secrets Manager, GCP Secret Manager)
- Enable HTTPS/TLS for API
- Implement API rate limiting & authentication
- Enable database encryption at rest
- Set up VPC endpoints for private connectivity
- Regular security audits and dependency updates

## 🐛 Troubleshooting

### Database Connection Error
```bash
# Check database is running
make logs-db

# Reset database
docker-compose down -v
make up
```

### API Won't Start
```bash
# Check logs
make logs

# Verify environment variables
cat .env

# Test connection
make psql
```

### Tests Failing
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run with verbose output
pytest tests/ -vv
```

## 📚 API Examples

### Get All Data (with Pagination)
```bash
curl "http://localhost:8000/data?limit=20&offset=0"
```

### Filter by Source
```bash
curl "http://localhost:8000/data?source=api_source&limit=10"
```

### Health Check
```bash
curl http://localhost:8000/health
```

### View Statistics
```bash
curl "http://localhost:8000/stats?limit=5"
```

## 📝 Next Steps (P1/P2)

1. **Add Third Data Source** (P1.1)
   - Implement RSS feed ingestion
   - Add another API endpoint source
   - Unify schema across 3+ sources

2. **Enhance Recovery** (P1.2)
   - Implement failure injection testing
   - Add detailed error logging
   - Build recovery dashboard

3. **Add Observability** (P2.4)
   - Prometheus metrics endpoint
   - Distributed tracing with OpenTelemetry
   - Dashboard with Grafana

4. **Production Hardening** (P2.5)
   - GitHub Actions CI/CD
   - Automated image publishing
   - Deployment automation

## 📧 Support & Questions

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review test files for usage examples

## 📄 License

This project is provided as-is for the Kasparro hiring process.

---

**Last Updated**: December 2024  
**Status**: Production-Ready (P0 + P1 Core)
