"""LED AI Copilot - FastAPI Application Entry Point."""

from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from database.connection import engine, Base
from routers import projects, components, copilot, parsers as parser_router, knowledge, export

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    logger.info("=== LED AI Copilot 시작 ===")

    # Create DB tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Create upload/export directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.EXPORT_DIR, exist_ok=True)

    # Initialize vector store
    try:
        from rag.vector_store import VectorStore
        vs = VectorStore()
        vs.initialize()
        logger.info("Vector store initialized")
    except Exception as e:
        logger.warning(f"Vector store init failed (non-fatal): {e}")

    # Seed design principles if DB is empty
    try:
        from services.knowledge_service import seed_initial_knowledge
        seed_initial_knowledge()
        logger.info("Knowledge base seeded")
    except Exception as e:
        logger.warning(f"Knowledge seed failed (non-fatal): {e}")

    yield

    logger.info("=== LED AI Copilot 종료 ===")


app = FastAPI(
    title="LED AI Copilot",
    description="LED 제품 개발 AI 코파일럿 - 회로 설계, RF, 인증, 양산 지원",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(components.router, prefix="/api/components", tags=["components"])
app.include_router(copilot.router, prefix="/api/copilot", tags=["copilot"])
app.include_router(parser_router.router, prefix="/api/parse", tags=["parsers"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(export.router, prefix="/api/export", tags=["export"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "LED AI Copilot",
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    return {"message": "LED AI Copilot API", "docs": "/docs"}
