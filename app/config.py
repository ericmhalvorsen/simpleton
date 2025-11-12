"""Configuration management for Simpleton LLM Service"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Keys
    api_keys: str = "changeme"  # Comma-separated list

    # Ollama Configuration
    ollama_host: str = "http://localhost:11434"
    ollama_base_url: str = "http://localhost:11434"

    # Default Models
    default_inference_model: str = "qwen2.5:7b"
    default_embedding_model: str = "nomic-embed-text"
    default_vision_model: str = "llava"
    default_audio_model: str = "base"  # Whisper model size: tiny, base, small, medium, large

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000

    # Logging
    log_level: str = "INFO"

    # RAG Configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""  # Optional for local deployments
    default_collection: str = "documents"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5

    # Cache Configuration
    redis_url: str = "redis://localhost:6379"
    cache_enabled: bool = True
    cache_ttl: int = 3600  # Default TTL in seconds (1 hour)
    cache_embedding_ttl: int = 86400  # 24 hours for embeddings
    cache_inference_ttl: int = 3600  # 1 hour for inference

    # Monitoring Configuration
    monitoring_enabled: bool = True
    metrics_retention_hours: int = 168  # 7 days
    alert_error_rate_threshold: float = 0.1  # 10% error rate
    alert_response_time_threshold: float = 5.0  # 5 seconds

    @property
    def valid_api_keys(self) -> List[str]:
        """Parse API keys from comma-separated string"""
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]


# Global settings instance
settings = Settings()
