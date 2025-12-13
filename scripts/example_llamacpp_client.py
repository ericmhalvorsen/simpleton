#!/usr/bin/env python3
"""
example_llamacpp_client.py - Example client for llama.cpp multi-GPU server

This script demonstrates how to interact with the llama.cpp server API
for completions, chat, streaming, and embeddings.

Usage:
    python scripts/example_llamacpp_client.py
"""

import asyncio
import json
import time
from typing import AsyncIterator

import httpx


class LlamaCppClient:
    """
    Client for llama.cpp server with multi-GPU support.

    The llama.cpp server provides an OpenAI-compatible API, so this client
    can be used as a drop-in replacement for OpenAI's API client.
    """

    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Initialize the client.

        Args:
            base_url: Base URL of the llama.cpp server (default: http://localhost:8080)
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 min timeout for large models

    async def health_check(self) -> bool:
        """Check if the server is healthy and responding."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False

    async def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        response = await self.client.get(f"{self.base_url}/v1/models")
        return response.json()

    async def completion(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: list[str] | None = None,
    ) -> dict:
        """
        Generate a text completion.

        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic, 1.0+ = creative)
            top_p: Nucleus sampling threshold
            stop: List of stop sequences

        Returns:
            Dictionary with completion results
        """
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }
        if stop:
            payload["stop"] = stop

        response = await self.client.post(
            f"{self.base_url}/v1/completions",
            json=payload,
        )
        return response.json()

    async def chat_completion(
        self,
        messages: list[dict],
        max_tokens: int = 100,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> dict | AsyncIterator[dict]:
        """
        Generate a chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream the response

        Returns:
            Dictionary with chat results, or async iterator if streaming
        """
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }

        if stream:
            return self._stream_chat(payload)
        else:
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
            )
            return response.json()

    async def _stream_chat(self, payload: dict) -> AsyncIterator[dict]:
        """Internal method to handle streaming chat responses."""
        async with self.client.stream(
            "POST",
            f"{self.base_url}/v1/chat/completions",
            json=payload,
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    if data == "[DONE]":
                        break
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        continue

    async def embeddings(self, text: str) -> list[float]:
        """
        Generate embeddings for the given text.

        Args:
            text: Input text to embed

        Returns:
            List of embedding values
        """
        payload = {"input": text}
        response = await self.client.post(
            f"{self.base_url}/v1/embeddings",
            json=payload,
        )
        result = response.json()
        return result["data"][0]["embedding"]

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def main():
    """Run example usage of the llama.cpp client."""
    client = LlamaCppClient()

    print("=" * 60)
    print("llama.cpp Multi-GPU Client Examples")
    print("=" * 60)
    print()

    # Example 1: Health check
    print("1. Health Check")
    print("-" * 60)
    is_healthy = await client.health_check()
    if not is_healthy:
        print("❌ Server is not responding. Is llama.cpp running?")
        print("   Start it with: docker-compose -f docker-compose.llamacpp.yml up -d")
        return
    print("✓ Server is healthy")
    print()

    # Example 2: Model info
    print("2. Model Information")
    print("-" * 60)
    model_info = await client.get_model_info()
    print(json.dumps(model_info, indent=2))
    print()

    # Example 3: Simple completion
    print("3. Text Completion")
    print("-" * 60)
    prompt = "The key to successful multi-GPU inference is"
    print(f"Prompt: {prompt}")
    print()

    start_time = time.time()
    result = await client.completion(
        prompt=prompt,
        max_tokens=100,
        temperature=0.7,
    )
    elapsed = time.time() - start_time

    completion_text = result["choices"][0]["text"]
    tokens_generated = result["usage"]["completion_tokens"]
    tokens_per_sec = tokens_generated / elapsed if elapsed > 0 else 0

    print(f"Response: {completion_text}")
    print()
    print(f"Stats: {tokens_generated} tokens in {elapsed:.2f}s ({tokens_per_sec:.2f} tok/s)")
    print()

    # Example 4: Chat completion
    print("4. Chat Completion")
    print("-" * 60)
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Explain tensor parallelism in simple terms."},
    ]
    print(f"User: {messages[1]['content']}")
    print()

    result = await client.chat_completion(
        messages=messages,
        max_tokens=150,
        temperature=0.7,
    )

    response = result["choices"][0]["message"]["content"]
    print(f"Assistant: {response}")
    print()

    # Example 5: Streaming chat
    print("5. Streaming Chat Completion")
    print("-" * 60)
    messages = [
        {"role": "user", "content": "Count from 1 to 10."},
    ]
    print(f"User: {messages[0]['content']}")
    print("Assistant: ", end="", flush=True)

    async for chunk in await client.chat_completion(
        messages=messages,
        max_tokens=50,
        temperature=0.3,
        stream=True,
    ):
        if "choices" in chunk and len(chunk["choices"]) > 0:
            delta = chunk["choices"][0].get("delta", {})
            content = delta.get("content", "")
            print(content, end="", flush=True)

    print()
    print()

    # Example 6: Embeddings
    print("6. Text Embeddings")
    print("-" * 60)
    text = "Multi-GPU inference with llama.cpp"
    print(f"Text: {text}")

    embedding = await client.embeddings(text)
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 10 values: {embedding[:10]}")
    print()

    # Cleanup
    await client.close()

    print("=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  - Integrate this client into your application")
    print("  - Monitor GPU usage: ./scripts/monitor-gpus.sh")
    print("  - Tune performance: Adjust tensor-split, context size, etc.")


if __name__ == "__main__":
    asyncio.run(main())
