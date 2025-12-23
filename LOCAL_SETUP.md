# 🐍 Local Development Setup Guide

Complete guide for running Kasparro Backend without Docker using Python virtual environment.

## ✅ Virtual Environment Created

Your virtual environment is ready at: `.venv/`

**Python Version**: 3.13.7  
**Location**: `C:/Users/Sabiha Anjum/Documents/kasparro-backend-Sabiha-Anjum/.venv/`

### All Dependencies Installed
✅ FastAPI  
✅ Uvicorn  
✅ SQLAlchemy  
✅ Pydantic  
✅ PostgreSQL driver (psycopg2)  
✅ Testing tools (pytest, pytest-asyncio)  
✅ Code quality tools (black, flake8, mypy)  

---

## 🚀 Running the Backend

### Step 1: Activate Virtual Environment

**Windows PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
.venv\Scripts\activate.bat
```

**Expected Output:**
```
(.venv) C:\Users\Sabiha Anjum\Documents\kasparro-backend-Sabiha-Anjum>
```

### Step 2: Setup PostgreSQL Database

**Option A: Using Docker (Just Database)**
```powershell
docker run -d `
  -e POSTGRES_PASSWORD=password `
  -e POSTGRES_DB=kasparro `
  -p 5432:5432 `
  --name kasparro_db `
  postgres:15
```

**Option B: Using Local PostgreSQL**
- Ensure PostgreSQL 15+ is installed and running
- Create database: `createdb -U postgres kasparro`
- Create user: `createuser kasparro`

### Step 3: Configure Environment

```powershell
# Copy example configuration
cp .env.example .env

# Edit .env with your settings
# Update DATABASE_URL if using different credentials
```

**Default .env:**
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/kasparro
API_KEY=test-key-for-development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

### Step 4: Initialize Database

```powershell
# Create tables in database
python -c "from src.core.database import init_db; init_db()"
```

### Step 5: Start the Backend

```powershell
# Run the FastAPI application
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Step 6: Test the API

Open a **new PowerShell window** (keeping the first one running):

```powershell
# Health check
curl http://localhost:8000/health

# Get data
curl "http://localhost:8000/data?limit=5"

# View stats
curl http://localhost:8000/stats
```

---

## 🌐 Access API Documentation

Visit these URLs in your browser:

```
http://localhost:8000/docs        # Swagger UI (interactive)
http://localhost:8000/redoc       # ReDoc (alternative)
```

You can test endpoints directly from these interfaces!

---

## 🧪 Running Tests

### All Tests
```powershell
pytest tests/ -v
```

### With Coverage Report
```powershell
pytest tests/ -v --cov=src --cov-report=html
```

View report:
```powershell
start htmlcov/index.html
```

### Specific Tests
```powershell
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_api.py -v

# Specific test function
pytest tests/unit/test_api.py::test_health_endpoint_db_connected -v
```

---

## 🔧 Common Development Commands

### Code Quality

```powershell
# Format code
black src tests

# Sort imports
isort src tests

# Check style
flake8 src tests

# Type checking
mypy src --ignore-missing-imports

# All checks
black src tests && isort src tests && flake8 src tests && mypy src --ignore-missing-imports
```

### Database Management

```powershell
# Connect to database
psql -U postgres -d kasparro -h localhost

# View tables
psql -U postgres -d kasparro -h localhost -c "\dt"

# Reset database
psql -U postgres -d kasparro -h localhost -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

### ETL Operations

```powershell
# Run ETL manually
python run_etl.py

# Check ETL status
curl http://localhost:8000/stats
```

---

## 🐛 Troubleshooting

### Virtual Environment Not Activating

**PowerShell Error**: "cannot be loaded because running scripts is disabled"

**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\.venv\Scripts\Activate.ps1
```

### Database Connection Error

**Error**: "could not connect to server"

**Solution**:
1. Check PostgreSQL is running: `pg_isready -h localhost`
2. Verify DATABASE_URL in .env
3. Recreate database if needed

### Port 8000 Already in Use

**Error**: "Address already in use"

**Solution**:
```powershell
# Use different port
python -m uvicorn src.api.main:app --reload --port 8001
```

### Pydantic Validation Error

**Error**: "validation error" when sending requests

**Solution**:
1. Check request format matches API docs
2. Verify all required fields are present
3. Check data types are correct

### Module Not Found Error

**Error**: "ModuleNotFoundError: No module named 'src'"

**Solution**:
```powershell
# Ensure you're in the project root directory
cd kasparro-backend-Sabiha-Anjum

# Reinstall packages
pip install -r requirements.txt
```

---

## 📊 Development Workflow

### Daily Development Loop

1. **Activate environment** (if not already)
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. **Start backend** (Terminal 1)
   ```powershell
   python -m uvicorn src.api.main:app --reload
   ```

3. **Make code changes** (Your editor)
   - Code reloads automatically with `--reload`

4. **Run tests** (Terminal 2)
   ```powershell
   pytest tests/ -v
   ```

5. **Check code quality** (Terminal 2)
   ```powershell
   black src && isort src && flake8 src
   ```

6. **Stop backend** (Terminal 1)
   ```
   Press Ctrl+C
   ```

### Adding New Dependencies

```powershell
# Install new package
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt
```

---

## 📝 Environment Variables

Create `.env` in project root:

```
# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/kasparro

# API Configuration
API_KEY=your-api-key-here
API_TIMEOUT_SECONDS=30

# ETL Configuration
ETL_BATCH_SIZE=100
ETL_CHECKPOINT_INTERVAL=100

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

---

## 🔍 Verifying Installation

Run this to verify everything works:

```powershell
# Activate environment
.\.venv\Scripts\Activate.ps1

# Run basic checks
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import sqlalchemy; print('SQLAlchemy:', sqlalchemy.__version__)"
python -c "import pydantic; print('Pydantic:', pydantic.__version__)"

# Initialize database
python -c "from src.core.database import init_db; init_db(); print('Database initialized!')"

# Run tests
pytest tests/ -v --tb=short
```

---

## 💾 Deactivating Environment

When done developing:

```powershell
deactivate
```

Your shell will return to normal (no `.venv` prefix).

To activate again later, just run:
```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 🔄 Updating Dependencies

If dependencies change (someone updates requirements.txt):

```powershell
# Activate environment
.\.venv\Scripts\Activate.ps1

# Install/update dependencies
pip install -r requirements.txt
```

---

## 📚 IDE Configuration

### VS Code Configuration

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
  "python.formatting.provider": "black",
  "python.linting.flake8Enabled": true,
  "python.linting.pylintEnabled": false,
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.python"
  }
}
```

### PyCharm Configuration

1. Go to Settings → Project → Python Interpreter
2. Click ⚙️ → Add
3. Select "Existing Environment"
4. Navigate to `.venv/Scripts/python.exe`
5. Click OK

---

## 🚀 Comparison: Virtual Env vs Docker

| Feature | Virtual Env | Docker |
|---------|-------------|--------|
| Setup Time | 2 minutes | 5 minutes |
| Performance | Native | Slight overhead |
| Database | External | Included |
| Isolation | Good | Excellent |
| Cross-Platform | Fair | Excellent |
| Learning Curve | Easy | Moderate |

**Use Virtual Env when:**
- Developing locally
- Want fast iteration
- Have PostgreSQL installed locally
- Prefer native performance

**Use Docker when:**
- Need exact production environment
- Don't have PostgreSQL installed
- Want isolated setup
- Planning deployment

---

## ✅ You're All Set!

Your development environment is ready. Start with:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn src.api.main:app --reload
```

Then visit: http://localhost:8000/docs

Happy coding! 🚀
