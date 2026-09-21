import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger("price_tracker.main")

from backend.app.config import settings
from backend.app.database_firebase import init_firestore, is_mock_firestore
from backend.app.api import auth_router, products_router
from backend.app.api.alerts import router as alerts_router
from backend.app.mock_store import mock_store_router
from backend.app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Firestore database client
    init_firestore()
    # Start periodic price checking scheduler
    start_scheduler()
    yield
    # Shutdown: Stop scheduler
    stop_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "A full-featured Price Drop Tracker & Alert API powered by Google Cloud Firestore (Firebase). "
        "Tracks e-commerce products, records price movements in subcollections, and triggers drop alerts."
    ),
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    """Ensure static web files and HTML are never served stale by browser caches."""
    response = await call_next(request)
    if request.url.path.endswith((".js", ".html", ".css")) or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Mount API routes
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(alerts_router)
app.include_router(mock_store_router)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Ensure all unhandled backend exceptions return clean structured JSON with descriptive details."""
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Server error: {str(exc)}"}
    )


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint to verify system and database status."""
    return {
        "status": "healthy",
        "database": "firestore" if not is_mock_firestore() else "firestore_mock_mode",
        "scheduler_enabled": settings.SCHEDULER_ENABLED
    }


# Mount frontend static directory if present
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
