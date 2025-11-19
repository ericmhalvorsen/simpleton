# Simpleton

Self-hosted API service for running open-source LLMs. Built on FastAPI and Ollama.

## Quick Start

1. Start the service:
```bash
./start.sh
```

2. Set your API key in `.env`:
```bash
API_KEYS=your-generated-key-here
```

3. Pull models:
```bash
docker exec -it simpleton-ollama ollama pull qwen2.5:7b
docker exec -it simpleton-ollama ollama pull nomic-embed-text
```

4. Access:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## Usage

```bash
curl -X POST http://localhost:8000/inference/generate \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing",
    "model": "qwen2.5:7b"
  }'
```

## API Endpoints

**Inference:**
- `POST /inference/generate` - Generate text
- `POST /inference/chat` - Chat completion

**Embeddings:**
- `POST /embeddings/` - Create embeddings

**RAG:**
- `POST /rag/ingest` - Ingest documents
- `POST /rag/query` - Query with RAG
- `POST /rag/search` - Semantic search

**Vision:**
- `POST /vision/analyze` - Analyze images

**Audio:**
- `POST /audio/transcribe` - Transcribe audio
- `POST /audio/translate` - Translate audio

**Code Completion:**
- `POST /completion/inline` - FIM code completion

**Analytics:**
- `GET /analytics/stats` - Service statistics
- `GET /metrics` - Prometheus metrics

See `/docs` for full API documentation.

## Configuration

Edit `.env`:
```bash
API_KEYS=your-key
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_INFERENCE_MODEL=qwen2.5:7b
DEFAULT_EMBEDDING_MODEL=nomic-embed-text
```

## Development

```bash
# Local development with uv
uv sync
uv run uvicorn app.main:app --reload
```
