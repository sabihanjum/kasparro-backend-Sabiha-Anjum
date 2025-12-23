# ⚡ Quick Reference - Virtual Environment Commands

Copy & paste these commands for common tasks.

## 🚀 First Time Setup (2 minutes)

```powershell
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Copy environment file
cp .env.example .env

# 3. Initialize database (ensure PostgreSQL is running)
python -c "from src.core.database import init_db; init_db()"

# 4. Start backend
python -m uvicorn src.api.main:app --reload --port 8000
```

## 🌐 After Setup - Daily Development

### Terminal 1 (Backend Server)
```powershell
# Activate environment
.\.venv\Scripts\Activate.ps1

# Start server (auto-reloads on code changes)
python -m uvicorn src.api.main:app --reload --port 8000
```

### Terminal 2 (Testing & Utilities)
```powershell
# Activate environment
.\.venv\Scripts\Activate.ps1

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/unit/test_api.py -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Code quality checks
black src tests
isort src tests
flake8 src tests
mypy src --ignore-missing-imports

# Format code
black src && isort src

# Run ETL manually
python run_etl.py
```

## 📊 API Testing

```powershell
# Health check
curl http://localhost:8000/health

# Get data
curl "http://localhost:8000/data?limit=10&offset=0"

# Filter by source
curl "http://localhost:8000/data?source=jsonplaceholder&limit=5"

# View statistics
curl http://localhost:8000/stats

# Interactive API docs
start http://localhost:8000/docs
```

## 🗄️ Database Commands

```powershell
# Connect to PostgreSQL CLI
psql -U postgres -d kasparro -h localhost

# View all tables
psql -U postgres -d kasparro -h localhost -c "\dt"

# Reset database (WARNING: Deletes all data!)
psql -U postgres -d kasparro -h localhost -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Count records
psql -U postgres -d kasparro -h localhost -c "SELECT COUNT(*) FROM normalized_data;"
```

## 🧹 Cleanup & Maintenance

```powershell
# Deactivate environment
deactivate

# Remove pycache
Remove-Item -Recurse -Force __pycache__, .pytest_cache, .mypy_cache

# Clear Python cache files
Get-ChildItem -Recurse *.pyc | Remove-Item -Force

# Reinstall all packages
pip install -r requirements.txt --force-reinstall

# Update packages
pip list --outdated
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

## 🆘 Troubleshooting

```powershell
# Check Python version
python --version

# Check virtual environment is active
python -c "import sys; print(sys.prefix)"

# Verify package installation
pip list

# Check PostgreSQL connection
psql -U postgres -c "\conninfo"

# Kill process on port 8000 (if stuck)
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## 📝 Useful Information

**Activate Environment:**
- PowerShell: `.\.venv\Scripts\Activate.ps1`
- CMD: `.venv\Scripts\activate.bat`
- Bash: `source .venv/Scripts/activate`

**Virtual Environment Location:**
- `.venv/Scripts/python.exe` - Python executable
- `.venv/Scripts/pip.exe` - Package manager
- `.venv/Lib/` - Installed packages

**Key Directories:**
- `src/` - Source code
- `tests/` - Test suite
- `data/` - Sample data
- `.venv/` - Virtual environment

**Configuration Files:**
- `.env` - Environment variables
- `requirements.txt` - Python dependencies
- `pytest.ini` - Test configuration
- `setup.cfg` - Tool configuration

---

**Status**: Ready for development ✅  
**Time to Running**: 2 minutes  
**All Dependencies**: Installed ✅
