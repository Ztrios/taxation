from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    # OpenAI/vLLM Configuration
    openai_api_key: str
    openai_base_url: str
    model_name: str
    filter_model_name: str = "meta-llama/llama-3.2-1b-instruct"
    
    # Weaviate Configuration
    weaviate_url: str
    weaviate_api_key: str
    collection_name: str

    # Gemini Configuration
    gemini_api_key: str
    embedding_model: str
    expected_embedding_dim: int
    
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
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()
