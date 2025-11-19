"""Code completion endpoints for inline FIM (Fill-in-the-Middle) completion"""

import logging
from collections.abc import AsyncIterator

import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.auth import RequireAPIKey
from app.config import settings
from app.models import CodeCompletionRequest, CodeCompletionResponse
from app.utils.cache import get_cache_client
from app.utils.monitoring import CACHE_HITS, CACHE_MISSES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/completion", tags=["completion"])


def format_fim_prompt(prefix: str, suffix: str, language: str | None = None) -> str:
    """
    Format a FIM (Fill-in-the-Middle) prompt for code completion.

    Different models use different FIM token formats:
    - DeepSeek Coder: <｜fim▁begin｜>prefix<｜fim▁hole｜>suffix<｜fim▁end｜>
    - CodeLlama: <PRE> prefix <SUF> suffix <MID>
    - StarCoder: <fim_prefix>prefix<fim_suffix>suffix<fim_middle>

    For Ollama, we use a simplified prompt format that works well with most models.
    """
    # Language context helps with completion quality
    lang_context = f"# Language: {language}\n" if language else ""

    # Use a general FIM-style prompt that works with most code models in Ollama
    if suffix:
        # Full FIM with suffix context
        prompt = f"{lang_context}<fim_prefix>{prefix}<fim_suffix>{suffix}<fim_middle>"
    else:
        # Simple completion without suffix
        prompt = f"{lang_context}{prefix}"

    return prompt


async def stream_completion_response(response: httpx.Response) -> AsyncIterator[str]:
    """Stream completion response from Ollama"""
    async for line in response.aiter_lines():
        if line:
            yield f"data: {line}\n\n"


@router.post("/inline", response_model=CodeCompletionResponse)
async def inline_completion(
    request: CodeCompletionRequest,
    api_key: RequireAPIKey,
):
    """
    Generate inline code completion using FIM (Fill-in-the-Middle).

    This endpoint is optimized for speed with:
    - Low temperature for deterministic completions
    - Small max_tokens for fast generation
    - FIM-capable models (qwen2.5-coder, deepseek-coder, codellama)
    - Aggressive caching for repeated patterns
    - Optional streaming for real-time feedback

    Recommended models for 64GB VRAM:
    - qwen2.5-coder:7b (fast, excellent quality)
    - deepseek-coder:6.7b (very fast, good FIM)
    - codellama:13b (balanced, great for code)
    """
    model = request.model or settings.default_completion_model

    # Use configured defaults, allow override
    temperature = request.temperature if request.temperature is not None else settings.completion_temperature
    max_tokens = request.max_tokens or settings.completion_max_tokens

    # Format FIM prompt
    fim_prompt = format_fim_prompt(request.prefix, request.suffix, request.language)

    # Build Ollama request payload optimized for speed
    payload = {
        "model": model,
        "prompt": fim_prompt,
        "stream": request.stream,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
            "num_ctx": settings.completion_num_ctx,
            "top_p": 0.95,  # Slightly focused for code
            "top_k": 50,  # Reasonable diversity
            "stop": ["\n\n", "```", "<|endoftext|>", "<fim_pad>", "<fim_middle>", "<fim_suffix>"],  # Stop tokens
        },
    }

    # Initialize cache client
    cache = get_cache_client(settings.redis_url, settings.cache_enabled)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:  # Short timeout for speed
            if request.stream:
                # Streaming responses are not cached
                response = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json=payload,
                    timeout=30.0,
                )
                response.raise_for_status()
                return StreamingResponse(
                    stream_completion_response(response),
                    media_type="text/event-stream",
                )
            else:
                # Non-streaming response - check cache first
                cache_key_data = {
                    "model": model,
                    "prefix": request.prefix[:500],  # Limit cache key size
                    "suffix": request.suffix[:200],
                    "language": request.language,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }

                cached_response = cache.get("completion", cache_key_data)

                if cached_response is not None:
                    # Cache hit - instant response!
                    CACHE_HITS.labels(cache_type="completion").inc()
                    logger.debug(f"Cache hit for completion (model: {model})")
                    return CodeCompletionResponse(**cached_response)

                # Cache miss - call Ollama
                CACHE_MISSES.labels(cache_type="completion").inc()
                logger.debug(f"Cache miss for completion (model: {model})")

                response = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                # Calculate tokens per second for performance monitoring
                tokens_per_second = None
                if data.get("eval_count") and data.get("eval_duration"):
                    # eval_duration is in nanoseconds
                    duration_seconds = data["eval_duration"] / 1_000_000_000
                    tokens_per_second = data["eval_count"] / duration_seconds if duration_seconds > 0 else None

                # Build response
                completion_response = {
                    "completion": data.get("response", ""),
                    "model": data.get("model", model),
                    "done": data.get("done", True),
                    "language": request.language,
                    "total_duration": data.get("total_duration"),
                    "eval_count": data.get("eval_count"),
                    "tokens_per_second": tokens_per_second,
                }

                # Cache the response for faster subsequent requests
                cache.set("completion", cache_key_data, completion_response, ttl=settings.cache_completion_ttl)

                logger.info(
                    f"Completion generated: {data.get('eval_count', 0)} tokens "
                    f"in {data.get('total_duration', 0) / 1_000_000:.0f}ms "
                    f"({tokens_per_second:.1f} tok/s)" if tokens_per_second else ""
                )

                return CodeCompletionResponse(**completion_response)

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
        logger.error(f"Unexpected error in code completion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.get("/models")
async def list_completion_models(api_key: RequireAPIKey):
    """
    List recommended code completion models for your hardware.

    Returns models optimized for 64GB VRAM with FIM capabilities.
    """
    return {
        "current_model": settings.default_completion_model,
        "recommended_models": {
            "fastest": {
                "name": "qwen2.5-coder:1.5b",
                "description": "Extremely fast, good for simple completions",
                "vram_usage": "~2GB",
                "speed": "very high",
            },
            "balanced": {
                "name": "qwen2.5-coder:7b",
                "description": "Excellent balance of speed and quality (recommended)",
                "vram_usage": "~8GB",
                "speed": "high",
            },
            "quality": {
                "name": "deepseek-coder:6.7b-instruct",
                "description": "High quality code completions with FIM",
                "vram_usage": "~8GB",
                "speed": "high",
            },
            "large": {
                "name": "codellama:13b-code",
                "description": "Best quality for complex completions",
                "vram_usage": "~16GB",
                "speed": "medium",
            },
            "maximum": {
                "name": "deepseek-coder:33b",
                "description": "Maximum quality for your 64GB VRAM",
                "vram_usage": "~40GB",
                "speed": "low",
            },
        },
        "installation_command": "ollama pull <model_name>",
        "note": "Smaller models (1.5b-7b) recommended for fastest inline completion",
    }
