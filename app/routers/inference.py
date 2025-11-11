"""Inference endpoints for text generation"""

import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
import json
from typing import AsyncIterator

from app.auth import RequireAPIKey
from app.config import settings
from app.models import (
    InferenceRequest,
    InferenceResponse,
    ChatRequest,
    ChatResponse,
)

router = APIRouter(prefix="/inference", tags=["inference"])


async def stream_ollama_response(response: httpx.Response) -> AsyncIterator[str]:
    """Stream response from Ollama"""
    async for line in response.aiter_lines():
        if line:
            yield f"data: {line}\n\n"


@router.post("/generate", response_model=InferenceResponse)
async def generate_text(
    request: InferenceRequest,
    api_key: RequireAPIKey,
):
    """
    Generate text completion from a prompt.

    This endpoint uses Ollama's generate API to produce text completions.
    Supports streaming and various sampling parameters.
    """
    model = request.model or settings.default_inference_model

    # Build Ollama request payload
    payload = {
        "model": model,
        "prompt": request.prompt,
        "stream": request.stream,
    }

    # Add optional parameters
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

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            if request.stream:
                # Streaming response
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
                # Non-streaming response
                response = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
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
    """
    Generate chat completion from a conversation history.

    This endpoint uses Ollama's chat API for more structured conversations
    with system prompts and multi-turn dialogues.
    """
    model = request.model or settings.default_inference_model

    # Build Ollama request payload
    payload = {
        "model": model,
        "messages": [msg.model_dump() for msg in request.messages],
        "stream": request.stream,
    }

    # Add optional parameters
    options = {}
    if request.temperature is not None:
        options["temperature"] = request.temperature
    if request.max_tokens is not None:
        options["num_predict"] = request.max_tokens

    if options:
        payload["options"] = options

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            if request.stream:
                # Streaming response
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
                # Non-streaming response
                response = await client.post(
                    f"{settings.ollama_base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
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
