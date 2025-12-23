# 🚀 Quick Start Guide

Get your Kasparro Backend running in **5 minutes**.

## Option 1: Using Docker (Recommended)

### 1. Clone & Navigate
```bash
cd kasparro-backend-Sabiha-Anjum
```

### 2. Start Services
```bash
make up
```

The system is now running! Wait for database initialization (~10 seconds).

### 3. Test It
```bash
# Health check
curl http://localhost:8000/health

# Get data
curl "http://localhost:8000/data?limit=5"

# View stats
curl http://localhost:8000/stats

# Interactive docs
open http://localhost:8000/docs
```

### 4. Stop Services
```bash
make down
```

---

## Option 2: Local Development

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
cp .env.example .env
# Edit .env with your settings (database connection, API key, etc.)
```

### 3. Start PostgreSQL
```bash
# Using Docker (just the database)
docker run -d \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=kasparro \
  -p 5432:5432 \
  postgres:15
```

### 4. Run Application
```bash
python -m uvicorn src.api.main:app --reload
```

API available at: `http://localhost:8000`

### 5. Run Tests
```bash
make test
```

---

## Key Features

✅ **Data Ingestion**
- Ingest from APIs and CSV files
- Automatic schema normalization
- Incremental processing with checkpoints

✅ **REST API**
```
GET  /health      - Health check
GET  /data        - Get data (paginated, filterable)
GET  /stats       - ETL statistics
GET  /docs        - Interactive API documentation
```

✅ **Production Ready**
- Docker containerization
- Database migrations
- Error handling & logging
- Test suite included

---

## Common Tasks

### View Logs
```bash
make logs          # Backend logs
make logs-db       # Database logs
```

### Access Database
```bash
make psql          # Open PostgreSQL CLI
```

### Run Tests
```bash
make test          # All tests with coverage
make test-unit     # Unit tests only
```

### Code Quality
```bash
make lint          # Check code
make format        # Auto-format code
make type-check    # Type checking
```

### Create Admin User (Example)
```bash
make shell         # Open container shell
python -c "from src.core.database import init_db; init_db()"
```

---

## Configuration

### API Key Setup
```bash
# In .env file
API_KEY=your-actual-api-key-here
```

### Database Configuration
```bash
# In .env file
DATABASE_URL=postgresql://postgres:password@localhost:5432/kasparro
```

### ETL Sources
Sources are configured in [src/core/etl_config.py](src/core/etl_config.py):
- JSONPlaceholder API (demo)
- GitHub API (trending repos)
- Sample CSV file

---

## API Examples

### Paginated Data Retrieval
```bash
curl "http://localhost:8000/data?limit=10&offset=0"
```

### Filter by Source
```bash
curl "http://localhost:8000/data?source=jsonplaceholder"
```

### Get Statistics
```bash
curl "http://localhost:8000/stats?limit=10"
```

### Health Status
```bash
curl http://localhost:8000/health
```

---

## Next Steps

1. **Review Architecture**: See [README.md](README.md) for detailed design
2. **Deploy to Cloud**: See [DEPLOYMENT.md](DEPLOYMENT.md) for AWS/GCP/Azure setup
3. **Add Data Source**: Configure additional API or CSV sources in [src/core/etl_config.py](src/core/etl_config.py)
4. **Enable Scheduling**: Set up cloud scheduler for automated ETL runs
5. **Monitor & Alert**: Setup CloudWatch/Stackdriver metrics and alarms

---

## Troubleshooting

### Port Already in Use
```bash
# Change port in docker-compose.yml or use:
make down
```

### Database Connection Error
```bash
# Wait longer for database to start
sleep 15
curl http://localhost:8000/health
```

### Tests Failing
```bash
# Ensure dependencies installed
pip install -r requirements.txt
make test -v
```

---

## Docker Commands

```bash
make up              # Start services
make down            # Stop services  
make restart         # Restart services
make clean           # Remove everything (including data)
make logs            # View logs
make shell           # Enter container
```

---

**That's it! Your backend is running.** 🎉

For detailed documentation, see [README.md](README.md)
