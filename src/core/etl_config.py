"""ETL configuration for different data sources."""
from typing import Dict, Any

# API Sources Configuration
API_SOURCES: Dict[str, Dict[str, Any]] = {
    "jsonplaceholder": {
        "type": "api",
        "url": "https://jsonplaceholder.typicode.com/posts",
        "description": "JSONPlaceholder - Free fake REST API",
        "headers": {
            "Content-Type": "application/json",
        },
        "enabled": True,
    },
    "github_trends": {
        "type": "api",
        "url": "https://api.github.com/search/repositories?q=stars:>5000&sort=stars&order=desc&per_page=10",
        "description": "GitHub trending repositories",
        "headers": {
            "Accept": "application/vnd.github.v3+json",
        },
        "enabled": True,
    },
}

# CSV Sources Configuration
CSV_SOURCES: Dict[str, Dict[str, Any]] = {
    "sample_data": {
        "type": "csv",
        "path": "data/sample.csv",
        "description": "Sample CSV data for testing",
        "enabled": True,
    },
}

# Combined sources for ETL
ETL_SOURCES = {**API_SOURCES, **CSV_SOURCES}

# ETL Configuration
ETL_CONFIG = {
    "batch_size": 100,
    "checkpoint_interval": 100,
    "retry_attempts": 3,
    "timeout_seconds": 30,
}
