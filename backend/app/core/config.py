import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "CivicAI Karnataka"
    
    # JWT & Security
    SECRET_KEY: str = "karnataka_civic_grievance_management_ai_secret_key_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/civic_karnataka"
    
    # CORS Origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Image uploads settings
    UPLOAD_DIR: str = "static/uploads"
    
    # AI models settings
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    YOLO_MODEL: str = "yolov8n.pt"  # falls back to local execution
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
