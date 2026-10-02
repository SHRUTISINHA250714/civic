import os
# Bypassing the TensorFlow/Keras Keras 3 compatibility issue
os.environ["USE_TF"] = "NO"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TORCH"] = "1"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import sys
from pathlib import Path

# Ensure root workspace is in sys.path so 'backend.app...' imports work from any cwd
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.config import settings
from backend.app.routers import auth, complaints, dashboard, officers, notifications, predictive

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CivicAI Karnataka – AI-Powered Smart Civic Grievance Management System Backend API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Setup
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Mount Static Files (to serve uploaded images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(complaints.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(officers.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)
app.include_router(predictive.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def startup_db_check():
    """Startup check with retry/backoff for Neon serverless cold starts."""
    import time
    from sqlalchemy import text
    from backend.app.core.database import engine

    max_retries = 3
    retry_delay = 2.0
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[DB Startup Check] Connecting to database (Attempt {attempt}/{max_retries})...")
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("[DB Startup Check] ✓ Database connection established successfully.")
            return
        except Exception as e:
            print(f"[DB Startup Check] ⚠️ Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                print(f"[DB Startup Check] Retrying in {retry_delay}s for serverless wake-up...")
                time.sleep(retry_delay)
            else:
                print("[DB Startup Check] ❌ Failed to connect to database after max retries.")
                raise e

@app.get("/")
def read_root():
    return {
        "message": "Welcome to CivicAI Karnataka Backend API Portal",
        "swagger_docs": "/docs",
        "redoc": "/redoc"
    }
