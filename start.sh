#!/bin/bash

# Simpleton LLM Service Startup Script

set -e

echo "Starting Simpleton LLM Service..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and set your API_KEYS before continuing!"
    echo "   Generate a secure key with: openssl rand -hex 32"
    echo ""
    read -p "Press enter to continue after setting your API keys..."
fi

# Start services
echo "Starting Docker containers..."
docker-compose up -d

echo ""
echo "✅ Services started!"
echo ""
echo "Ollama is running at: http://localhost:11434"
echo "Simpleton API is running at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "Next steps:"
echo "1. Pull a model: docker exec -it simpleton-ollama ollama pull qwen2.5:7b"
echo "2. Pull embedding model: docker exec -it simpleton-ollama ollama pull nomic-embed-text"
echo "3. Test the API at http://localhost:8000/docs"
echo ""
echo "View logs:"
echo "  docker-compose logs -f simpleton"
echo "  docker-compose logs -f ollama"
echo ""
