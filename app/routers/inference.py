"""Text generation endpoints"""

import logging
from collections.abc import AsyncIterator

import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.auth import RequireAPIKey
from app.config import settings
from app.models import (
    ChatRequest,
    ChatResponse,
    InferenceRequest,
    InferenceResponse,
)
from app.utils.cache import get_cache_client
from app.utils.monitoring import CACHE_HITS, CACHE_MISSES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/inference", tags=["inference"])


async def stream_ollama_response(response: httpx.Response) -> AsyncIterator[str]:
    async for line in response.aiter_lines():
        if line:
            yield f"data: {line}\n\n"


@router.post("/generate", response_model=InferenceResponse)
async def generate_text(
    request: InferenceRequest,
    api_key: RequireAPIKey,
):
    model = request.model or settings.default_inference_model

    payload = {
        "model": model,
        "prompt": request.prompt,
        "stream": request.stream,
    }

    options = {}
    if request.temperature is not None:
        options["temperature"] = request.temperature
    if request.top_p is not None:
        options["top_p"] = request.top_p
    if request.top_k is not None:
        options["top_k"] = request.top_k
    if request.max_tokens is not None:
        options["num_predict"] = request.max_tokens

    if options:
        payload["options"] = options

    if request.system:
        payload["system"] = request.system
    if request.context:
        payload["context"] = request.context

    cache = get_cache_client(settings.redis_url, settings.cache_enabled)

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            if request.stream:
                response = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json=payload,
                    timeout=300.0,
                )
                response.raise_for_status()
                return StreamingResponse(
                    stream_ollama_response(response),
                    media_type="text/event-stream",
                )
            else:
                cache_key_data = {
                    "model": model,
                    "prompt": request.prompt,
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                    "top_k": request.top_k,
                    "max_tokens": request.max_tokens,
                    "system": request.system,
                }

                cached_response = cache.get("inference", cache_key_data)

                if cached_response is not None:
                    CACHE_HITS.labels(cache_type="inference").inc()
                    logger.debug(f"Cache hit for inference (model: {model})")
                    return InferenceResponse(**cached_response)

                CACHE_MISSES.labels(cache_type="inference").inc()
                logger.debug(f"Cache miss for inference (model: {model})")

                response = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                cache.set("inference", cache_key_data, data, ttl=settings.cache_inference_ttl)

                return InferenceResponse(**data)

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


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    api_key: RequireAPIKey,
):
    model = request.model or settings.default_inference_model

    payload = {
        "model": model,
        "messages": [msg.model_dump() for msg in request.messages],
        "stream": request.stream,
    }

    options = {}
    if request.temperature is not None:
        options["temperature"] = request.temperature
    if request.max_tokens is not None:
        options["num_predict"] = request.max_tokens

    if options:
        payload["options"] = options

    cache = get_cache_client(settings.redis_url, settings.cache_enabled)

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            if request.stream:
                response = await client.post(
                    f"{settings.ollama_base_url}/api/chat",
                    json=payload,
                    timeout=300.0,
                )
                response.raise_for_status()
                return StreamingResponse(
                    stream_ollama_response(response),
                    media_type="text/event-stream",
                )
            else:
                cache_key_data = {
                    "model": model,
                    "messages": [msg.model_dump() for msg in request.messages],
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                }

                cached_response = cache.get("chat", cache_key_data)

                if cached_response is not None:
                    CACHE_HITS.labels(cache_type="chat").inc()
                    logger.debug(f"Cache hit for chat (model: {model})")
                    return ChatResponse(**cached_response)

                CACHE_MISSES.labels(cache_type="chat").inc()
                logger.debug(f"Cache miss for chat (model: {model})")

                response = await client.post(
                    f"{settings.ollama_base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                cache.set("chat", cache_key_data, data, ttl=settings.cache_inference_ttl)

                return ChatResponse(**data)

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
