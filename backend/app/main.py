# Main application entry point - to be filled from main_app_py.txt
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.routes import router
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("Starting GitHub Issue Analyzer Backend")
    settings.validate()
    logger.info(f"Configuration validated. API Version: {settings.API_VERSION}")
    yield
    # Shutdown
    logger.info("Shutting down GitHub Issue Analyzer Backend")


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "details": str(exc) if settings.DEBUG else None
        }
    )


# Include routers
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
        "endpoints": {
            "analyze": "POST /api/v1/analyze",
            "analyze_batch": "POST /api/v1/analyze-batch",
            "stats": "GET /api/v1/stats",
            "health": "GET /api/v1/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("Hello")
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )