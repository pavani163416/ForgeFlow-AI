from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "ForgeFlow AI Backend"
    VERSION: str = "0.1.0"
    
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT_SECRET: str
    
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
