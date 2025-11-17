"""Pydantic models for request/response validation"""

from typing import Any

from pydantic import BaseModel, Field


# Inference Models
class InferenceRequest(BaseModel):
    """Request model for text inference/generation"""

    prompt: str = Field(..., description="The input prompt for the model")
    model: str | None = Field(None, description="Model to use (defaults to configured model)")
    stream: bool = Field(False, description="Stream the response")
    temperature: float | None = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int | None = Field(None, gt=0, description="Maximum tokens to generate")
    top_p: float | None = Field(None, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    top_k: int | None = Field(None, gt=0, description="Top-k sampling parameter")
    system: str | None = Field(None, description="System prompt")
    context: list[int] | None = Field(None, description="Context from previous conversation")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Explain quantum computing in simple terms",
                "model": "qwen2.5:7b",
                "temperature": 0.7,
                "max_tokens": 500,
            }
        }


class InferenceResponse(BaseModel):
    """Response model for text inference/generation"""

    model: str = Field(..., description="Model used for generation")
    response: str = Field(..., description="Generated text response")
    done: bool = Field(..., description="Whether generation is complete")
    context: list[int] | None = Field(None, description="Context for continuing conversation")
    total_duration: int | None = Field(None, description="Total duration in nanoseconds")
    load_duration: int | None = Field(None, description="Model load duration in nanoseconds")
    prompt_eval_count: int | None = Field(None, description="Number of tokens in prompt")
    eval_count: int | None = Field(None, description="Number of tokens generated")
    eval_duration: int | None = Field(None, description="Generation duration in nanoseconds")


# Embedding Models
class EmbeddingRequest(BaseModel):
    """Request model for generating embeddings"""

    input: str | list[str] = Field(..., description="Text or list of texts to embed")
    model: str | None = Field(
        None, description="Embedding model to use (defaults to configured model)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "input": "The quick brown fox jumps over the lazy dog",
                "model": "nomic-embed-text",
            }
        }


class EmbeddingData(BaseModel):
    """Individual embedding result"""

    embedding: list[float] = Field(..., description="The embedding vector")
    index: int = Field(..., description="Index of the text in the input list")


class EmbeddingResponse(BaseModel):
    """Response model for embeddings"""

    model: str = Field(..., description="Model used for embeddings")
    embeddings: list[list[float]] = Field(..., description="List of embedding vectors")
    total_duration: int | None = Field(None, description="Total duration in nanoseconds")


# Chat Models (for more structured conversations)
class ChatMessage(BaseModel):
    """A single message in a chat conversation"""

    role: str = Field(..., description="Role of the message sender (system/user/assistant)")
    content: str = Field(..., description="Content of the message")


class ChatRequest(BaseModel):
    """Request model for chat-based inference"""

    messages: list[ChatMessage] = Field(..., description="List of conversation messages")
    model: str | None = Field(None, description="Model to use (defaults to configured model)")
    stream: bool = Field(False, description="Stream the response")
    temperature: float | None = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int | None = Field(None, gt=0, description="Maximum tokens to generate")

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is the capital of France?"},
                ],
                "model": "qwen2.5:7b",
                "temperature": 0.7,
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat-based inference"""

    model: str = Field(..., description="Model used for generation")
    message: ChatMessage = Field(..., description="Generated message")
    done: bool = Field(..., description="Whether generation is complete")
    total_duration: int | None = Field(None, description="Total duration in nanoseconds")
    prompt_eval_count: int | None = Field(None, description="Number of tokens in prompt")
    eval_count: int | None = Field(None, description="Number of tokens generated")


# Health Check
class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Service status")
    ollama_status: str = Field(..., description="Ollama connection status")
    version: str = Field(..., description="Service version")


# Model Info
class ModelInfo(BaseModel):
    """Information about available models"""

    name: str = Field(..., description="Model name")
    size: int | None = Field(None, description="Model size in bytes")
    modified_at: str | None = Field(None, description="Last modification time")
    digest: str | None = Field(None, description="Model digest/hash")


class ModelsResponse(BaseModel):
    """Response containing list of available models"""

    models: list[ModelInfo] = Field(..., description="List of available models")


# RAG Models
class DocumentIngestRequest(BaseModel):
    """Request model for ingesting documents into RAG system"""

    content: str = Field(..., description="Document content to ingest")
    metadata: dict[str, Any] | None = Field(default_factory=dict, description="Document metadata")
    collection: str | None = Field(
        None, description="Collection name (defaults to configured collection)"
    )
    chunk_size: int | None = Field(
        None, description="Chunk size for splitting (defaults to configured size)"
    )
    chunk_overlap: int | None = Field(
        None, description="Overlap between chunks (defaults to configured overlap)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "This is a sample document about AI...",
                "metadata": {"source": "article.pdf", "author": "John Doe", "date": "2025-01-15"},
                "collection": "documents",
            }
        }


class DocumentChunk(BaseModel):
    """A single document chunk"""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    content: str = Field(..., description="Chunk content")
    metadata: dict[str, Any] = Field(..., description="Chunk metadata")


class DocumentIngestResponse(BaseModel):
    """Response model for document ingestion"""

    collection: str = Field(..., description="Collection name")
    chunks_created: int = Field(..., description="Number of chunks created")
    chunk_ids: list[str] = Field(..., description="List of created chunk IDs")
    embedding_model: str = Field(..., description="Model used for embeddings")


class RAGQueryRequest(BaseModel):
    """Request model for RAG-powered query"""

    query: str = Field(..., description="Query text")
    collection: str | None = Field(
        None, description="Collection to search (defaults to configured collection)"
    )
    top_k: int | None = Field(
        None, description="Number of results to retrieve (defaults to configured top_k)"
    )
    model: str | None = Field(
        None, description="Model for generation (defaults to configured model)"
    )
    system_prompt: str | None = Field(None, description="System prompt for generation")
    temperature: float | None = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int | None = Field(None, gt=0, description="Maximum tokens to generate")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the benefits of quantum computing?",
                "collection": "documents",
                "top_k": 3,
                "model": "qwen2.5:7b",
            }
        }


class SearchResult(BaseModel):
    """A single search result"""

    chunk_id: str = Field(..., description="Chunk identifier")
    content: str = Field(..., description="Chunk content")
    score: float = Field(..., description="Relevance score")
    metadata: dict[str, Any] = Field(..., description="Chunk metadata")


class RAGQueryResponse(BaseModel):
    """Response model for RAG-powered query"""

    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    sources: list[SearchResult] = Field(..., description="Source documents used")
    model: str = Field(..., description="Model used for generation")
    collection: str = Field(..., description="Collection searched")


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search"""

    query: str = Field(..., description="Search query")
    collection: str | None = Field(
        None, description="Collection to search (defaults to configured collection)"
    )
    top_k: int | None = Field(
        None, description="Number of results to return (defaults to configured top_k)"
    )
    score_threshold: float | None = Field(
        None, ge=0.0, le=1.0, description="Minimum similarity score"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "machine learning algorithms",
                "collection": "documents",
                "top_k": 5,
                "score_threshold": 0.7,
            }
        }


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search"""

    query: str = Field(..., description="Search query")
    results: list[SearchResult] = Field(..., description="Search results")
    collection: str = Field(..., description="Collection searched")
    total_results: int = Field(..., description="Total number of results")


class CollectionInfo(BaseModel):
    """Information about a collection"""

    name: str = Field(..., description="Collection name")
    vectors_count: int = Field(..., description="Number of vectors in collection")
    points_count: int = Field(..., description="Number of points in collection")


class CollectionsResponse(BaseModel):
    """Response containing list of collections"""

    collections: list[CollectionInfo] = Field(..., description="List of collections")


class CollectionDeleteResponse(BaseModel):
    """Response for collection deletion"""

    collection: str = Field(..., description="Deleted collection name")
    success: bool = Field(..., description="Whether deletion was successful")


# Vision Models
class VisionAnalyzeRequest(BaseModel):
    """Request model for vision analysis"""

    image: str = Field(..., description="Base64 encoded image or image URL")
    prompt: str = Field(..., description="Question or instruction about the image")
    model: str | None = Field(None, description="Vision model to use (defaults to llava)")
    temperature: float | None = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int | None = Field(None, gt=0, description="Maximum tokens to generate")

    class Config:
        json_schema_extra = {
            "example": {
                "image": "data:image/png;base64,iVBORw0KG...",
                "prompt": "What objects are in this image?",
                "model": "llava",
                "temperature": 0.7,
            }
        }


class VisionAnalyzeResponse(BaseModel):
    """Response model for vision analysis"""

    model: str = Field(..., description="Model used for analysis")
    response: str = Field(..., description="Generated description/answer")
    done: bool = Field(..., description="Whether generation is complete")
    total_duration: int | None = Field(None, description="Total duration in nanoseconds")
    eval_count: int | None = Field(None, description="Number of tokens generated")


class VisionCaptionRequest(BaseModel):
    """Request model for image captioning"""

    image: str = Field(..., description="Base64 encoded image or image URL")
    model: str | None = Field(None, description="Vision model to use (defaults to llava)")
    detail_level: str | None = Field(
        "normal", description="Caption detail level: brief, normal, or detailed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "image": "data:image/png;base64,iVBORw0KG...",
                "model": "llava",
                "detail_level": "normal",
            }
        }


class VisionCaptionResponse(BaseModel):
    """Response model for image captioning"""

    caption: str = Field(..., description="Generated image caption")
    model: str = Field(..., description="Model used for captioning")


class VisionOCRRequest(BaseModel):
    """Request model for OCR (text extraction from images)"""

    image: str = Field(..., description="Base64 encoded image or image URL")
    model: str | None = Field(None, description="Vision model to use (defaults to llava)")

    class Config:
        json_schema_extra = {
            "example": {"image": "data:image/png;base64,iVBORw0KG...", "model": "llava"}
        }


class VisionOCRResponse(BaseModel):
    """Response model for OCR"""

    text: str = Field(..., description="Extracted text from image")
    model: str = Field(..., description="Model used for OCR")


# Audio Models
class AudioTranscribeRequest(BaseModel):
    """Request model for audio transcription"""

    audio: str = Field(..., description="Base64 encoded audio file")
    language: str | None = Field(
        None, description="Language code (e.g., 'en', 'es', 'fr'). Auto-detect if not specified"
    )
    model: str | None = Field(
        None, description="Whisper model size (tiny, base, small, medium, large)"
    )
    task: str | None = Field(
        "transcribe", description="Task type: 'transcribe' or 'translate' (to English)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "audio": "data:audio/wav;base64,UklGRi...",
                "language": "en",
                "model": "base",
                "task": "transcribe",
            }
        }


class AudioTranscribeResponse(BaseModel):
    """Response model for audio transcription"""

    text: str = Field(..., description="Transcribed text")
    language: str | None = Field(None, description="Detected or specified language")
    duration: float | None = Field(None, description="Audio duration in seconds")
    model: str = Field(..., description="Model used for transcription")


class AudioTranslateRequest(BaseModel):
    """Request model for audio translation to English"""

    audio: str = Field(..., description="Base64 encoded audio file")
    model: str | None = Field(
        None, description="Whisper model size (tiny, base, small, medium, large)"
    )

    class Config:
        json_schema_extra = {
            "example": {"audio": "data:audio/wav;base64,UklGRi...", "model": "base"}
        }


class AudioTranslateResponse(BaseModel):
    """Response model for audio translation"""

    text: str = Field(..., description="Translated text (in English)")
    source_language: str | None = Field(None, description="Detected source language")
    duration: float | None = Field(None, description="Audio duration in seconds")
    model: str = Field(..., description="Model used for translation")
