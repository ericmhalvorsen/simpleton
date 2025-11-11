#!/usr/bin/env python3
"""
Example client for Simpleton LLM Service

Usage:
    python example_client.py

Make sure to set your API key in .env or export it:
    export SIMPLETON_API_KEY=your-api-key
"""

import asyncio
import os
import httpx
from typing import List


class SimpletonClient:
    """Simple client for interacting with Simpleton API"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str | None = None):
        self.base_url = base_url
        self.api_key = api_key or os.getenv("SIMPLETON_API_KEY", "changeme")
        self.headers = {"X-API-Key": self.api_key}

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict:
        """Generate text from a prompt"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/inference/generate",
                headers=self.headers,
                json={
                    "prompt": prompt,
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            return response.json()

    async def chat(
        self,
        messages: List[dict],
        model: str | None = None,
        temperature: float = 0.7,
    ) -> dict:
        """Chat completion with conversation history"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/inference/chat",
                headers=self.headers,
                json={
                    "messages": messages,
                    "model": model,
                    "temperature": temperature,
                },
            )
            response.raise_for_status()
            return response.json()

    async def embed(self, text: str | List[str], model: str | None = None) -> dict:
        """Generate embeddings for text"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/embeddings/",
                headers=self.headers,
                json={"input": text, "model": model},
            )
            response.raise_for_status()
            return response.json()

    async def list_models(self) -> dict:
        """List available models"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/models",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def health(self) -> dict:
        """Check service health"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()


async def main():
    """Run example requests"""
    client = SimpletonClient()

    print("=" * 60)
    print("Simpleton LLM Service - Example Client")
    print("=" * 60)

    # Check health
    print("\n1. Checking service health...")
    try:
        health = await client.health()
        print(f"   Status: {health['status']}")
        print(f"   Ollama: {health['ollama_status']}")
        print(f"   Version: {health['version']}")
    except Exception as e:
        print(f"   Error: {e}")
        print("\n   Make sure the service is running: docker-compose up -d")
        return

    # List models
    print("\n2. Listing available models...")
    try:
        models = await client.list_models()
        if models["models"]:
            for model in models["models"]:
                size_gb = model["size"] / (1024**3) if model["size"] else 0
                print(f"   - {model['name']} ({size_gb:.2f} GB)")
        else:
            print("   No models found. Pull a model first:")
            print("   docker exec simpleton-ollama ollama pull qwen2.5:7b")
            return
    except Exception as e:
        print(f"   Error: {e}")
        return

    # Generate text
    print("\n3. Generating text...")
    try:
        result = await client.generate(
            prompt="Write a haiku about coding",
            temperature=0.8,
            max_tokens=100,
        )
        print(f"   Model: {result['model']}")
        print(f"   Response:\n{result['response']}")
        if result.get("eval_count"):
            print(f"   Tokens generated: {result['eval_count']}")
    except Exception as e:
        print(f"   Error: {e}")

    # Chat completion
    print("\n4. Chat completion...")
    try:
        result = await client.chat(
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": "What is a REST API in one sentence?"},
            ]
        )
        print(f"   Model: {result['model']}")
        print(f"   Response: {result['message']['content']}")
    except Exception as e:
        print(f"   Error: {e}")

    # Generate embeddings
    print("\n5. Generating embeddings...")
    try:
        result = await client.embed("Hello, world!")
        print(f"   Model: {result['model']}")
        print(f"   Embedding dimension: {len(result['embeddings'][0])}")
        print(f"   First 5 values: {result['embeddings'][0][:5]}")
    except Exception as e:
        print(f"   Error: {e}")
        if "model" in str(e).lower():
            print("   Note: Make sure you have an embedding model installed:")
            print("   docker exec simpleton-ollama ollama pull nomic-embed-text")

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
