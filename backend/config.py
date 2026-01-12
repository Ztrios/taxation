from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        # Avoid warnings for fields like model_name/model_hf_path
        "protected_namespaces": ("settings_",),
    }

    # OpenAI/vLLM Configuration
    openai_api_key: str
    openai_base_url: str
    model_name: str
    
    # Weaviate Configuration
    weaviate_url: str
    weaviate_api_key: str
    cohere_apikey: Optional[str] = ""
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Token Configuration
    max_tokens: int = 30000
    model_hf_path: str
    
    # Application Configuration
    upload_dir: str = "./uploads"
settings = Settings()
