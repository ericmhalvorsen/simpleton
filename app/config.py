"""Configuration management"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    api_keys: str = "changeme"
    ollama_host: str = "http://localhost:11434"
    ollama_base_url: str = "http://localhost:11434"
    default_inference_model: str = "qwen2.5:7b"
    default_embedding_model: str = "nomic-embed-text"
    default_vision_model: str = "llava"
    default_audio_model: str = "base"
    default_completion_model: str = "qwen2.5-coder:7b"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    default_collection: str = "documents"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5
    redis_url: str = "redis://localhost:6379"
    cache_enabled: bool = True
    cache_ttl: int = 3600
    cache_embedding_ttl: int = 86400
    cache_inference_ttl: int = 3600
    cache_completion_ttl: int = 7200
    completion_max_tokens: int = 256
    completion_temperature: float = 0.2
    completion_num_ctx: int = 4096
    completion_num_predict: int = 256
    monitoring_enabled: bool = True
    metrics_retention_hours: int = 168
    alert_error_rate_threshold: float = 0.1
    alert_response_time_threshold: float = 5.0
    notifications_enabled: bool = True
    ntfy_url: str = "http://localhost:8080"
    ntfy_topic: str = ""
    notify_on_startup: bool = True
    notify_on_alerts: bool = True
    notify_on_requests: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    @property
    def valid_api_keys(self) -> list[str]:
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]


settings = Settings()
