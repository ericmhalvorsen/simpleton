"""Configuration management for Simpleton LLM Service"""

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    default_completion_model: str = "qwen2.5-coder:7b"  # FIM-capable code completion model

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
    cache_completion_ttl: int = 7200  # 2 hours for code completions

    # Code Completion Configuration
    completion_max_tokens: int = 256  # Maximum tokens for completion (keep small for speed)
    completion_temperature: float = 0.2  # Lower temperature for more deterministic completions
    completion_num_ctx: int = 4096  # Context window size for completion model
    completion_num_predict: int = 256  # Number of tokens to predict

    # Monitoring Configuration
    monitoring_enabled: bool = True
    metrics_retention_hours: int = 168  # 7 days
    alert_error_rate_threshold: float = 0.1  # 10% error rate
    alert_response_time_threshold: float = 5.0  # 5 seconds

    # Notification Configuration
    notifications_enabled: bool = True
    ntfy_url: str = "http://localhost:8080"  # Use http://ntfy:80 inside Docker
    ntfy_topic: str = ""  # Your topic name (e.g., simpleton-alerts)
    notify_on_startup: bool = True
    notify_on_alerts: bool = True
    notify_on_requests: bool = False  # Set to True to get notified on every API call
    telegram_bot_token: str = ""  # Optional: Telegram bot token
    telegram_chat_id: str = ""  # Optional: Telegram chat ID

    @property
    def valid_api_keys(self) -> list[str]:
        """Parse API keys from comma-separated string"""
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]


# Global settings instance
settings = Settings()
