"""
GitHub Issue Analyzer - FastAPI Application
Core application package
"""

from fastapi import FastAPI
from typing import Optional

__version__ = "1.0.0"

# Lazy imports for performance
_app: Optional[FastAPI] = None

def get_app() -> FastAPI:
    """Get or create FastAPI application instance"""
    global _app
    if _app is None:
        from app.core.config import settings
        from app.api.routes import router
        from app.utils.logger import setup_logger
        
        setup_logger()
        _app = FastAPI(
            title="GitHub Issue Analyzer API",
            description="AI-powered analysis of GitHub issues using Google Gemini",
            version=__version__,
            docs_url="/docs",
            openapi_url="/openapi.json"
        )
        _app.include_router(router, prefix="/api/v1")
    return _app

__all__ = ["get_app"]
