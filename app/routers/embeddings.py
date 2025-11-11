"""Embeddings endpoints for vector generation"""

import httpx
from fastapi import APIRouter, HTTPException, status
from typing import List

from app.auth import RequireAPIKey
from app.config import settings
from app.models import EmbeddingRequest, EmbeddingResponse

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

    try:
        embeddings = []
        total_duration = 0

        async with httpx.AsyncClient(timeout=120.0) as client:
            # Process each text
            for text in texts:
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

                embeddings.append(data["embedding"])
                if "total_duration" in data:
                    total_duration += data["total_duration"]

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
    texts: List[str],
    model: str | None = None,
    api_key: RequireAPIKey = None,
):
    """
    Generate embeddings for a batch of texts.

    Alternative endpoint with simpler interface for batch processing.
    Just send a list of strings directly.
    """
    request = EmbeddingRequest(input=texts, model=model)
    return await create_embeddings(request, api_key)
