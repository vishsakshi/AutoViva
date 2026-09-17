import os
from pathlib import Path
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

# Resolve absolute path to .env file regardless of current working directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_candidates = [
    BASE_DIR / ".env",
    BASE_DIR / "backend" / ".env",
    Path("backend/.env"),
    Path(".env")
]

selected_env_file = ".env"
for candidate in env_candidates:
    if candidate.exists():
        selected_env_file = str(candidate)
        break

class Settings(BaseSettings):
    PROJECT_NAME: str = "AutoViva API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # MongoDB
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "vivabot_db")
    
    # Security & Auth
    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecretjwtkey_change_me")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # LLM Settings (Configurable Provider: OpenAI, Ollama, DeepSeek, Local, Mock)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai_compatible")
    LLM_API_URL: str = os.getenv("LLM_API_URL", "https://api.openai.com/v1")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen2.5:3b")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
    
    # Environment & Storage
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000")
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "data/vector_store")

    model_config = ConfigDict(env_file=selected_env_file, extra="ignore")

settings = Settings()
