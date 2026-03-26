"""FastAPI application entry point for the LED Product Development AI Copilot."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database.connection import init_db
from rag.vector_store import VectorStore

from routers.projects import router as projects_router
from routers.components import router as components_router
from routers.copilot import router as copilot_router
from routers.parsers import router as parsers_router
from routers.knowledge import router as knowledge_router
from routers.export import router as export_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # ── Startup ──
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize vector store
    try:
        store = VectorStore.get_instance()
        store.initialize()
        logger.info("Vector store initialized")
    except Exception as e:
        logger.warning(f"Vector store initialization failed (non-fatal): {e}")

    yield

    # ── Shutdown ──
    logger.info("Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Copilot backend for LED lighting product development",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects_router)
app.include_router(components_router)
app.include_router(copilot_router)
app.include_router(parsers_router)
app.include_router(knowledge_router)
app.include_router(export_router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    store = VectorStore.get_instance()
    collections = store.list_collections() if store.client else []

    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "database": "connected",
        "vector_store": {
            "connected": store.client is not None,
            "collections": collections,
        },
        "anthropic_configured": bool(settings.ANTHROPIC_API_KEY),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
