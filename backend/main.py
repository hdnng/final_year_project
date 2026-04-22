"""
Camera AI Detection API — application entry point.

Initializes FastAPI, registers middleware, and mounts all routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from database.database import engine
import models

from api.router import (
    ai_result_router,
    camera_router,
    frame_router,
    history_router,
    statistics_router,
    user_router,
)

# ── Database ────────────────────────────────────────────────
models.Base.metadata.create_all(bind=engine)

# ── Application ─────────────────────────────────────────────
app = FastAPI(
    title="Camera AI Detection API",
    description="Production-grade API for classroom attention monitoring",
    version="2.0.0",
)

# ── CORS ────────────────────────────────────────────────────
if settings.is_production:
    allowed_origins = settings.ALLOWED_ORIGINS or ["https://yourdomain.com"]
else:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

# ── Routers ─────────────────────────────────────────────────
app.include_router(user_router.router)
app.include_router(camera_router.router)
app.include_router(frame_router.router)
app.include_router(statistics_router.router)
app.include_router(history_router.router)
app.include_router(ai_result_router.router)


# ── Health Check ────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}