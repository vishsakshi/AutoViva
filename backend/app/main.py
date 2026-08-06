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
    questions,
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
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
app.include_router(questions.router, prefix=api_prefix)
app.include_router(viva.router, prefix=api_prefix)
app.include_router(faculty_viva.router, prefix=api_prefix)
app.include_router(evaluation.router, prefix=api_prefix)

app.include_router(analytics.router, prefix=api_prefix)
app.include_router(knowledge.router, prefix=api_prefix)

