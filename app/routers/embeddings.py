"""Embeddings endpoints for vector generation"""

import logging

import httpx
from fastapi import APIRouter, HTTPException, Security, status

from app.auth import RequireAPIKey, validate_api_key
from app.config import settings
from app.models import EmbeddingRequest, EmbeddingResponse
from app.utils.cache import get_cache_client
from app.utils.monitoring import CACHE_HITS, CACHE_MISSES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/embeddings", tags=["embeddings"])


@router.post("/", response_model=EmbeddingResponse)
async def create_embeddings(
    request: EmbeddingRequest,
    api_key: RequireAPIKey,
):
    """
    Generate embeddings for text input.

    This endpoint converts text into vector embeddings using Ollama's embedding models.
    Supports both single strings and batches of texts.

    The embeddings can be used for:
    - Semantic search
    - Text similarity comparison
    - RAG (Retrieval Augmented Generation) applications
    - Clustering and classification
    """
    model = request.model or settings.default_embedding_model

    # Convert single input to list for consistent processing
    texts = [request.input] if isinstance(request.input, str) else request.input

    # Initialize cache client
    cache = get_cache_client(settings.redis_url, settings.cache_enabled)

    try:
        embeddings = []
        total_duration = 0

        # Process each text (with caching)
        for text in texts:
            # Check cache first
            cache_key_data = {"model": model, "text": text}
            cached_embedding = cache.get("embedding", cache_key_data)

            if cached_embedding is not None:
                # Cache hit
                CACHE_HITS.labels(cache_type="embedding").inc()
                logger.debug(f"Cache hit for embedding (model: {model})")
                embeddings.append(cached_embedding)
                continue

            # Cache miss - call Ollama
            CACHE_MISSES.labels(cache_type="embedding").inc()
            logger.debug(f"Cache miss for embedding (model: {model})")

            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "model": model,
                    "prompt": text,
                }

                response = await client.post(
                    f"{settings.ollama_base_url}/api/embeddings",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                embedding = data["embedding"]
                embeddings.append(embedding)

                if "total_duration" in data:
                    total_duration += data["total_duration"]

                # Cache the embedding
                cache.set("embedding", cache_key_data, embedding, ttl=settings.cache_embedding_ttl)

        return EmbeddingResponse(
            model=model,
            embeddings=embeddings,
            total_duration=total_duration if total_duration > 0 else None,
        )

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
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected response format from Ollama: missing {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.post("/batch", response_model=EmbeddingResponse)
async def create_batch_embeddings(
    texts: list[str],
    model: str | None = None,
    api_key: RequireAPIKey = Security(validate_api_key),
):
    """
    Generate embeddings for a batch of texts.

    Alternative endpoint with simpler interface for batch processing.
    Just send a list of strings directly.
    """
    request = EmbeddingRequest(input=texts, model=model)
    return await create_embeddings(request, api_key)
