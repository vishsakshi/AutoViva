import sys
import io

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
elif hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
elif hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.db import connect_to_mongo, close_mongo_connection
from app.routes import (
    health,
    auth,
    faculty,
    student,
    viva,
    faculty_viva,
    evaluation,
    analytics,
    knowledge,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS Configuration
raw_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
origins = list(set(raw_origins + ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in origins or settings.ENVIRONMENT == "production" else origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "title": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }

# Include API Routers under /api prefix
api_prefix = settings.API_V1_STR
app.include_router(health.router, prefix=api_prefix)
app.include_router(auth.router, prefix=api_prefix)
app.include_router(faculty.router, prefix=api_prefix)
app.include_router(student.router, prefix=api_prefix)
app.include_router(viva.router, prefix=api_prefix)
app.include_router(faculty_viva.router, prefix=api_prefix)
app.include_router(evaluation.router, prefix=api_prefix)
app.include_router(analytics.router, prefix=api_prefix)
app.include_router(knowledge.router, prefix=api_prefix)
