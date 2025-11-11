# Simpleton - Personal LLM Service

A self-hosted API service for running open-source LLMs. Built on FastAPI and Ollama.

Redo this whole thing

## Quick Start

### Prerequisites

- Docker and Docker Compose
- [mise](https://mise.jdx.dev/) - Task runner (optional but recommended)
- (Optional) NVIDIA GPU with Docker GPU support for better performance

### Installation

1. Install mise (optional but recommended):
```bash
curl https://mise.run | sh
```

2. Clone the repository:
```bash
git clone <your-repo-url>
cd simpleton
```

3. Start the service:
```bash
mise run start
# Or without mise:
./start.sh
```

4. Edit `.env` and set your API keys:
```bash
# Generate a secure key
openssl rand -hex 32

# Add to .env
API_KEYS=your-generated-key-here
```

5. Pull your desired models:
```bash
# Using mise
mise run pull-models

# Or manually
docker exec -it simpleton-ollama ollama pull qwen2.5:7b
docker exec -it simpleton-ollama ollama pull llama3.1:8b
docker exec -it simpleton-ollama ollama pull mistral:7b

# For embeddings
docker exec -it simpleton-ollama ollama pull nomic-embed-text
docker exec -it simpleton-ollama ollama pull mxbai-embed-large
```

6. Access the API:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Ollama: http://localhost:11434

## Model Recommendations

### General Purpose Models (2025)

| Model | Size | Best For | VRAM Required |
|-------|------|----------|---------------|
| Qwen 2.5 | 7B | All-around performance, coding | ~8 GB |
| Llama 3.1 | 8B | General tasks, reliable | ~8 GB |
| Mistral | 7B | Fast inference, good quality | ~8 GB |
| DeepSeek V2 | Various | Specialized tasks | Varies |

### Embedding Models

| Model | Best For |
|-------|----------|
| nomic-embed-text | General purpose, recommended |
| qwen3-embedding | Multilingual (#1 on MTEB) |
| mxbai-embed-large | High quality embeddings |

### Choosing a Model

The model you can run depends on your available VRAM:

- **8-16 GB VRAM**: 7B-8B models (qwen2.5:7b, llama3.1:8b, mistral:7b)
- **16-24 GB VRAM**: 13B models
- **24+ GB VRAM**: 70B models (quantized)
- **CPU only**: Use smaller quantized models, expect slower inference

Check available models: https://ollama.com/library

## Usage Examples

### Using cURL

#### Generate Text
```bash
curl -X POST http://localhost:8000/inference/generate \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in simple terms",
    "model": "qwen2.5:7b",
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

#### Chat Completion
```bash
curl -X POST http://localhost:8000/inference/chat \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is the capital of France?"}
    ],
    "model": "qwen2.5:7b"
  }'
```

#### Generate Embeddings
```bash
curl -X POST http://localhost:8000/embeddings/ \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "The quick brown fox jumps over the lazy dog",
    "model": "nomic-embed-text"
  }'
```

#### List Models
```bash
curl http://localhost:8000/models \
  -H "X-API-Key: your-api-key"
```

### Using Python

```python
import httpx

API_KEY = "your-api-key"
BASE_URL = "http://localhost:8000"

async def generate_text(prompt: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/inference/generate",
            headers={"X-API-Key": API_KEY},
            json={
                "prompt": prompt,
                "temperature": 0.7,
                "max_tokens": 500,
            }
        )
        return response.json()

async def create_embedding(text: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/embeddings/",
            headers={"X-API-Key": API_KEY},
            json={"input": text}
        )
        return response.json()
```

### Using JavaScript/TypeScript

```typescript
const API_KEY = "your-api-key";
const BASE_URL = "http://localhost:8000";

async function generateText(prompt: string) {
  const response = await fetch(`${BASE_URL}/inference/generate`, {
    method: "POST",
    headers: {
      "X-API-Key": API_KEY,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      prompt,
      temperature: 0.7,
      max_tokens: 500,
    }),
  });
  return await response.json();
}

async function createEmbedding(text: string) {
  const response = await fetch(`${BASE_URL}/embeddings/`, {
    method: "POST",
    headers: {
      "X-API-Key": API_KEY,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ input: text }),
  });
  return await response.json();
}
```

## Configuration

Edit `.env` to configure the service:

```bash
# API Keys (comma-separated for multiple keys)
API_KEYS=key1,key2,key3

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_BASE_URL=http://localhost:11434

# Default Models
DEFAULT_INFERENCE_MODEL=qwen2.5:7b
DEFAULT_EMBEDDING_MODEL=nomic-embed-text

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Logging
LOG_LEVEL=INFO
```

## API Endpoints

### Public Endpoints
- `GET /` - Service information
- `GET /health` - Health check
- `GET /docs` - OpenAPI documentation

### Authenticated Endpoints
- `POST /inference/generate` - Generate text from prompt
- `POST /inference/chat` - Chat completion
- `POST /embeddings/` - Create embeddings
- `POST /embeddings/batch` - Batch embeddings
- `GET /models` - List available models

All authenticated endpoints require the `X-API-Key` header.

## Running Without Docker (Local Development with uv)

For local development, we use [uv](https://github.com/astral-sh/uv) - an extremely fast Python package installer and resolver.

### Why uv?

- **10-100x faster** than pip
- **Built-in virtual environment** management
- **Deterministic** dependency resolution
- **Drop-in replacement** for pip

### Setup

1. Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Install Ollama: https://ollama.com/download

3. Install dependencies:
```bash
mise run install
# Or manually:
uv sync
```

4. Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the service:
```bash
mise run run
# Or manually:
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Local Development Commands

```bash
mise run install      # Install dependencies
mise run dev          # Install with dev dependencies (pytest, ruff)
mise run run          # Run the service locally
mise run lint         # Run linting
mise run format       # Format code

# View all available tasks
mise tasks
```

## GPU Support

To enable GPU acceleration with NVIDIA GPUs:

1. Install NVIDIA Container Toolkit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

2. Uncomment the GPU section in `docker-compose.yml`:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

3. Restart the services:
```bash
docker-compose down
docker-compose up -d
```

## Troubleshooting

### Can't connect to Ollama
- Check if Ollama container is running: `docker ps`
- Check logs: `docker-compose logs ollama`
- Verify Ollama is accessible: `curl http://localhost:11434/api/tags`

### Model not found
- List available models: `docker exec simpleton-ollama ollama list`
- Pull the model: `docker exec simpleton-ollama ollama pull <model-name>`

### API returns 401 Unauthorized
- Verify your API key is set in `.env`
- Ensure you're sending the `X-API-Key` header
- Check the header value matches a key in `API_KEYS`

### Slow inference
- Consider using a smaller model
- Enable GPU support if available
- Check system resources: `docker stats`

### Out of memory
- Use a smaller model
- Reduce context length
- Close other applications using VRAM/RAM

## Development

### Project Structure
```
simpleton/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── config.py         # Configuration management
│   ├── auth.py           # Authentication
│   ├── models.py         # Pydantic models
│   └── routers/
│       ├── inference.py  # Inference endpoints
│       └── embeddings.py # Embedding endpoints
├── .env                  # Environment variables
├── .env.example         # Example configuration
├── .python-version      # Python version for uv
├── pyproject.toml       # Python dependencies and project metadata
├── mise.toml            # Task runner configuration
├── Dockerfile           # Service container (uses uv)
├── docker-compose.yml   # Docker orchestration
├── start.sh            # Startup script
└── example_client.py   # Example API client
```

### Running Tests
```bash
# Install dev dependencies
mise run dev
# Or manually:
uv sync --extra dev

# Run tests
uv run pytest

# Or check API health
mise run test
```

## Security Considerations

1. **Change Default API Keys**: Always use strong, randomly generated API keys
2. **Use HTTPS**: In production, run behind a reverse proxy with SSL/TLS
3. **Firewall**: Restrict access to trusted networks/IPs
4. **Resource Limits**: Set appropriate memory/CPU limits in production
5. **Rate Limiting**: Consider adding rate limiting for production use

## License

See LICENSE file for details.

## Contributing

Contributions welcome! Please open an issue or PR.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Ollama](https://ollama.com/)
- Inspired by the open-source LLM community
