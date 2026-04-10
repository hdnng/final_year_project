from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from database.database import engine
import models

from api.router import user_router
from api.router import camera_router
from api.router import statistics_router
from api.router import history_router

load_dotenv()

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Camera AI Detection API",
    description="Production-grade API with JWT security",
    version="1.0.0"
)

# CORS middleware - environment-based configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    # Production: restrict to specific origins
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
    allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]
    if not allowed_origins:
        # Fallback if not configured - restrict more strictly
        allowed_origins = ["https://yourdomain.com"]
else:
    # Development: allow all origins for easier testing
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,  # 10 minutes
)

app.include_router(user_router.router)
app.include_router(camera_router.router)
app.include_router(statistics_router.router)
app.include_router(history_router.router)


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "environment": ENVIRONMENT}