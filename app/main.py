"""Simpleton - Personal LLM Service"""

import logging

import httpx
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.auth import RequireAPIKey
from app.config import settings
from app.models import HealthResponse, ModelInfo, ModelsResponse
from app.routers import analytics, audio, completion, embeddings, inference, rag, vision
from app.utils.monitoring import MonitoringMiddleware, export_prometheus_metrics, get_metrics_store
from app.utils.notifications import get_notification_service

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Simpleton LLM Service",
    description="Personal LLM inference and embedding service",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.monitoring_enabled:
    metrics_store = get_metrics_store(settings.metrics_retention_hours)
    app.add_middleware(MonitoringMiddleware, metrics_store=metrics_store)
    logger.info("Monitoring middleware enabled")

app.include_router(inference.router)
app.include_router(embeddings.router)
app.include_router(completion.router)
app.include_router(rag.router)
app.include_router(analytics.router)
app.include_router(vision.router)
app.include_router(audio.router)


# Startup/Shutdown Events
@app.on_event("startup")
async def startup_event():
    if settings.notifications_enabled and settings.notify_on_startup:
        try:
            notification_service = get_notification_service(
                ntfy_url=settings.ntfy_url,
                ntfy_topic=settings.ntfy_topic,
                telegram_bot_token=settings.telegram_bot_token,
                telegram_chat_id=settings.telegram_chat_id,
                enabled=settings.notifications_enabled,
            )
            await notification_service.send_startup(
                service_name="Simpleton",
                host=settings.host,
                port=settings.port,
            )
            logger.info("Startup notification sent")
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    if settings.notifications_enabled:
        try:
            notification_service = get_notification_service(
                ntfy_url=settings.ntfy_url,
                ntfy_topic=settings.ntfy_topic,
                telegram_bot_token=settings.telegram_bot_token,
                telegram_chat_id=settings.telegram_chat_id,
                enabled=settings.notifications_enabled,
            )
            await notification_service.send_shutdown(service_name="Simpleton")
            logger.info("Shutdown notification sent")
        except Exception as e:
            logger.error(f"Failed to send shutdown notification: {e}")


@app.get("/", response_model=dict)
async def root():
    return {
        "service": "Simpleton LLM Service",
        "version": __version__,
        "description": "Personal LLM inference and embedding service",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    ollama_status = "disconnected"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            if response.status_code == 200:
                ollama_status = "connected"
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")
        ollama_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy",
        ollama_status=ollama_status,
        version=__version__,
    )


@app.get("/metrics")
async def metrics():
    metrics_data, content_type = export_prometheus_metrics()
    return Response(content=metrics_data, media_type=content_type)


@app.get("/models", response_model=ModelsResponse)
async def list_models(api_key: RequireAPIKey):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            response.raise_for_status()
            data = response.json()

            models = [
                ModelInfo(
                    name=model.get("name"),
                    size=model.get("size"),
                    modified_at=model.get("modified_at"),
                    digest=model.get("digest"),
                )
                for model in data.get("models", [])
            ]

            return ModelsResponse(models=models)

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ollama API error: {e.response.text}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to Ollama: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
