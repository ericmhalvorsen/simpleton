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
- Qdrant Dashboard: http://localhost:6333/dashboard

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

## RAG (Retrieval-Augmented Generation)

Simpleton includes a powerful RAG pipeline with Qdrant vector database integration. This allows you to:
- Ingest and index documents
- Perform semantic search across your knowledge base
- Generate answers based on your documents

### RAG Architecture

The system uses three containers:
- **Simpleton API** - Orchestrates RAG operations
- **Ollama** - Generates embeddings and LLM responses
- **Qdrant** - Stores document embeddings (vector database)

Access points:
- Simpleton API: http://localhost:8000
- Qdrant API: http://localhost:6333
- Qdrant Dashboard: http://localhost:6333/dashboard

### Quick Start with RAG

#### 1. Ingest a Document

```bash
curl -X POST http://localhost:8000/rag/ingest \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Quantum computing uses quantum-mechanical phenomena such as superposition and entanglement to perform computation. Unlike classical computers that use bits (0 or 1), quantum computers use quantum bits or qubits that can exist in multiple states simultaneously.",
    "metadata": {
      "source": "quantum_computing.txt",
      "category": "technology",
      "date": "2025-01-15"
    },
    "collection": "documents"
  }'
```

**Response:**
```json
{
  "collection": "documents",
  "chunks_created": 1,
  "chunk_ids": ["uuid-1", "uuid-2"],
  "embedding_model": "nomic-embed-text"
}
```

#### 2. Query Your Documents (RAG)

```bash
curl -X POST http://localhost:8000/rag/query \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is quantum computing?",
    "collection": "documents",
    "top_k": 3,
    "model": "qwen2.5:7b"
  }'
```

**Response:**
```json
{
  "query": "What is quantum computing?",
  "answer": "Based on the provided context, quantum computing is...",
  "sources": [
    {
      "chunk_id": "uuid-1",
      "content": "Quantum computing uses quantum-mechanical phenomena...",
      "score": 0.92,
      "metadata": {"source": "quantum_computing.txt"}
    }
  ],
  "model": "qwen2.5:7b",
  "collection": "documents"
}
```

#### 3. Semantic Search (Without LLM)

```bash
curl -X POST http://localhost:8000/rag/search \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "quantum superposition",
    "collection": "documents",
    "top_k": 5,
    "score_threshold": 0.7
  }'
```

#### 4. List Collections

```bash
curl -X GET http://localhost:8000/rag/collections \
  -H "X-API-Key: your-api-key"
```

#### 5. Delete a Collection

```bash
curl -X DELETE http://localhost:8000/rag/collections/documents \
  -H "X-API-Key: your-api-key"
```

### RAG Configuration

Add to your `.env` file:

```bash
# Qdrant Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Optional, leave empty for local deployment

# RAG Settings
DEFAULT_COLLECTION=documents
CHUNK_SIZE=1000            # Characters per chunk
CHUNK_OVERLAP=200          # Overlap between chunks
TOP_K_RESULTS=5           # Number of results to retrieve
```

### Document Chunking Strategies

The RAG system automatically chunks large documents using intelligent strategies:

1. **Recursive (Default)**: Tries to preserve document structure
   - Splits by paragraphs first
   - Falls back to sentences if paragraphs are too large
   - Falls back to tokens as last resort

2. **Paragraph-based**: Splits on double newlines
3. **Sentence-based**: Splits on sentence boundaries
4. **Token-based**: Splits by approximate token count

You can control chunking behavior:
```json
{
  "content": "Your long document...",
  "chunk_size": 500,
  "chunk_overlap": 100
}
```

### Supported Document Formats

While the API accepts text content, you can parse various formats before ingestion:

- **PDF** - Using `pypdf` library
- **DOCX** - Using `python-docx` library
- **Markdown** - Converts to plain text
- **Plain Text** - Direct ingestion

Example workflow for PDF:
```python
from pypdf import PdfReader
import httpx

# Parse PDF
reader = PdfReader("document.pdf")
content = "\n\n".join([page.extract_text() for page in reader.pages])

# Ingest to RAG
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/rag/ingest",
        headers={"X-API-Key": "your-key"},
        json={
            "content": content,
            "metadata": {"source": "document.pdf", "pages": len(reader.pages)}
        }
    )
```

### RAG Use Cases

1. **Knowledge Base Q&A**: Index your documentation and let users ask questions
2. **Research Assistant**: Search through research papers and articles
3. **Customer Support**: Retrieve relevant answers from support documents
4. **Code Documentation**: Search through code documentation and examples
5. **Legal/Contract Analysis**: Find relevant clauses and information
6. **Meeting Notes**: Search through meeting transcripts and notes

### Python RAG Example

```python
import httpx

API_KEY = "your-api-key"
BASE_URL = "http://localhost:8000"

async def ingest_document(content: str, metadata: dict):
    """Ingest a document into the RAG system"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/rag/ingest",
            headers={"X-API-Key": API_KEY},
            json={
                "content": content,
                "metadata": metadata,
                "collection": "my_docs"
            }
        )
        return response.json()

async def query_documents(question: str):
    """Query documents with RAG"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/rag/query",
            headers={"X-API-Key": API_KEY},
            json={
                "query": question,
                "collection": "my_docs",
                "top_k": 3
            }
        )
        return response.json()

# Usage
await ingest_document(
    content="Your document content here...",
    metadata={"source": "guide.pdf", "author": "John Doe"}
)

result = await query_documents("What is the main topic?")
print(f"Answer: {result['answer']}")
print(f"Sources: {len(result['sources'])}")
```

### RAG Performance Tips

1. **Chunk Size**:
   - Smaller chunks (500-1000 chars) = More precise retrieval
   - Larger chunks (1000-2000 chars) = More context per result

2. **Overlap**:
   - 10-20% of chunk_size is recommended
   - Prevents information loss at chunk boundaries

3. **Top K**:
   - Start with 3-5 results
   - More results = more context but slower generation

4. **Embedding Model**:
   - `nomic-embed-text` - Fast, good quality (default)
   - `mxbai-embed-large` - Higher quality, slower
   - `qwen3-embedding` - Best for multilingual

5. **Collection Organization**:
   - Use separate collections for different document types
   - Add metadata for filtering (source, date, category, etc.)

## Audio Transcription & Translation

Simpleton includes audio processing capabilities using Whisper for transcription and translation.

### Quick Start with Audio

#### 1. Transcribe Audio (Base64)

```bash
# Transcribe with automatic language detection
curl -X POST http://localhost:8000/audio/transcribe \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "audio": "UklGRiQAAABXQVZFZm10...",
    "model": "base"
  }'
```

**Response:**
```json
{
  "text": "This is the transcribed text from the audio.",
  "language": "en",
  "duration": 12.5,
  "model": "base"
}
```

#### 2. Translate Audio to English

```bash
# Translate from any language to English
curl -X POST http://localhost:8000/audio/translate \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "audio": "UklGRiQAAABXQVZFZm10...",
    "model": "base"
  }'
```

#### 3. Upload Audio File

```bash
# Transcribe uploaded file
curl -X POST http://localhost:8000/audio/upload/transcribe \
  -H "X-API-Key: your-api-key" \
  -F "file=@meeting_recording.mp3" \
  -F "model=base"

# Translate uploaded file
curl -X POST http://localhost:8000/audio/upload/translate \
  -H "X-API-Key: your-api-key" \
  -F "file=@podcast.wav" \
  -F "model=small"
```

### Audio Configuration

Add to your `.env` file:

```bash
# Default Whisper model (tiny, base, small, medium, large)
DEFAULT_AUDIO_MODEL=base
```

### Whisper Model Sizes

Choose based on your accuracy vs. speed needs:

| Model | Size | Speed | Accuracy | Best For |
|-------|------|-------|----------|----------|
| tiny | 75MB | Fastest | Lowest | Quick drafts, real-time |
| base | 142MB | Fast | Good | General use (default) |
| small | 466MB | Medium | Better | Professional transcription |
| medium | 1.5GB | Slow | High | High-quality needs |
| large | 3GB | Slowest | Highest | Maximum accuracy |

Models are downloaded automatically on first use and cached globally.

### Supported Audio Formats

- WAV, MP3, M4A, FLAC, OGG, OPUS, WEBM
- Any format supported by ffmpeg

### Audio Use Cases

1. **Meeting Transcription**: Record and transcribe team meetings
2. **Podcast Processing**: Generate transcripts for podcasts
3. **Accessibility**: Create captions for video content
4. **Voice Notes**: Transcribe voice memos and notes
5. **Language Learning**: Transcribe and translate foreign language audio
6. **Documentation**: Convert recorded instructions to text

### Python Audio Example

```python
import httpx
import base64

API_KEY = "your-api-key"
BASE_URL = "http://localhost:8000"

async def transcribe_audio(audio_path: str):
    """Transcribe audio file"""
    # Read and encode audio
    with open(audio_path, "rb") as f:
        audio_data = base64.b64encode(f.read()).decode()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/audio/transcribe",
            headers={"X-API-Key": API_KEY},
            json={
                "audio": audio_data,
                "model": "base"
            }
        )
        return response.json()

async def translate_audio(audio_path: str):
    """Translate audio to English"""
    with open(audio_path, "rb") as f:
        audio_data = base64.b64encode(f.read()).decode()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/audio/translate",
            headers={"X-API-Key": API_KEY},
            json={
                "audio": audio_data,
                "model": "base"
            }
        )
        return response.json()

# Usage
result = await transcribe_audio("meeting.mp3")
print(f"Transcription: {result['text']}")
print(f"Language: {result['language']}")
```

### Audio Performance Tips

1. **Model Selection**:
   - Use `tiny` or `base` for real-time or near-real-time needs
   - Use `small` or `medium` for production transcription
   - Use `large` only when maximum accuracy is critical

2. **Audio Quality**:
   - Clear audio = better transcription accuracy
   - 16kHz or higher sample rate recommended
   - Reduce background noise when possible

3. **Language Hints**:
   - Specify language if known for faster processing
   - Omit language for automatic detection (90+ languages)

4. **File Size**:
   - Longer audio = longer processing time
   - Consider splitting very long files (>1 hour)

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

**Inference:**
- `POST /inference/generate` - Generate text from prompt
- `POST /inference/chat` - Chat completion

**Embeddings:**
- `POST /embeddings/` - Create embeddings
- `POST /embeddings/batch` - Batch embeddings

**RAG (Retrieval-Augmented Generation):**
- `POST /rag/ingest` - Ingest documents into vector database
- `POST /rag/query` - Query documents with LLM-powered answers
- `POST /rag/search` - Semantic search (without LLM)
- `GET /rag/collections` - List all document collections
- `DELETE /rag/collections/{name}` - Delete a collection

**Vision (Multimodal):**
- `POST /vision/analyze` - Analyze images with custom prompts
- `POST /vision/caption` - Generate image captions
- `POST /vision/ocr` - Extract text from images
- `POST /vision/upload` - Upload and analyze image files

**Audio (Multimodal):**
- `POST /audio/transcribe` - Transcribe audio to text (90+ languages)
- `POST /audio/translate` - Translate audio to English
- `POST /audio/upload/transcribe` - Upload and transcribe audio files
- `POST /audio/upload/translate` - Upload and translate audio files

**Analytics & Monitoring:**
- `GET /analytics/stats` - Service statistics
- `GET /analytics/errors` - Recent errors
- `GET /analytics/alerts` - Active alerts
- `GET /analytics/cache` - Cache statistics
- `DELETE /analytics/cache` - Clear cache
- `GET /metrics` - Prometheus metrics

**Models:**
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

### Can't connect to Qdrant
- Check if Qdrant container is running: `docker ps | grep qdrant`
- Check logs: `docker-compose logs qdrant`
- Verify Qdrant is accessible: `curl http://localhost:6333/collections`
- Access Qdrant dashboard: http://localhost:6333/dashboard

### Model not found
- List available models: `docker exec simpleton-ollama ollama list`
- Pull the model: `docker exec simpleton-ollama ollama pull <model-name>`

### API returns 401 Unauthorized
- Verify your API key is set in `.env`
- Ensure you're sending the `X-API-Key` header
- Check the header value matches a key in `API_KEYS`

### RAG query returns no results
- Verify documents are ingested: `curl http://localhost:8000/rag/collections -H "X-API-Key: your-key"`
- Check collection name matches between ingest and query
- Try lowering `score_threshold` in search requests
- Ensure embedding model is pulled: `docker exec simpleton-ollama ollama pull nomic-embed-text`

### Slow inference
- Consider using a smaller model
- Enable GPU support if available
- Check system resources: `docker stats`

### Out of memory
- Use a smaller model
- Reduce context length
- Reduce `top_k` results in RAG queries
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
│   ├── routers/
│   │   ├── inference.py  # Inference endpoints
│   │   ├── embeddings.py # Embedding endpoints
│   │   ├── rag.py        # RAG endpoints
│   │   ├── vision.py     # Vision (multimodal) endpoints
│   │   ├── audio.py      # Audio transcription/translation endpoints
│   │   └── analytics.py  # Analytics & monitoring endpoints
│   └── utils/
│       ├── document_parser.py  # Document parsing (PDF, DOCX, etc.)
│       ├── text_chunker.py     # Text chunking strategies
│       ├── qdrant_client.py    # Qdrant vector database client
│       ├── cache.py            # Redis caching client
│       └── monitoring.py       # Monitoring middleware & metrics
├── .env                  # Environment variables
├── .env.example         # Example configuration
├── .python-version      # Python version for uv
├── pyproject.toml       # Python dependencies and project metadata
├── mise.toml            # Task runner configuration
├── Dockerfile           # Service container (uses uv)
├── docker-compose.yml   # Docker orchestration (Simpleton + Ollama + Qdrant + Redis)
├── start.sh            # Startup script
├── example_client.py   # Example API client
├── IDEAS.md            # Enhancement ideas and roadmap
├── PHASE2_COMPLETE.md  # Phase 2 implementation summary
└── README.md           # This file
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
