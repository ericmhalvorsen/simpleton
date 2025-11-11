"""Pydantic models for request/response validation"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# Inference Models
class InferenceRequest(BaseModel):
    """Request model for text inference/generation"""

    prompt: str = Field(..., description="The input prompt for the model")
    model: Optional[str] = Field(None, description="Model to use (defaults to configured model)")
    stream: bool = Field(False, description="Stream the response")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens to generate")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    top_k: Optional[int] = Field(None, gt=0, description="Top-k sampling parameter")
    system: Optional[str] = Field(None, description="System prompt")
    context: Optional[List[int]] = Field(None, description="Context from previous conversation")

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
    context: Optional[List[int]] = Field(None, description="Context for continuing conversation")
    total_duration: Optional[int] = Field(None, description="Total duration in nanoseconds")
    load_duration: Optional[int] = Field(None, description="Model load duration in nanoseconds")
    prompt_eval_count: Optional[int] = Field(None, description="Number of tokens in prompt")
    eval_count: Optional[int] = Field(None, description="Number of tokens generated")
    eval_duration: Optional[int] = Field(None, description="Generation duration in nanoseconds")


# Embedding Models
class EmbeddingRequest(BaseModel):
    """Request model for generating embeddings"""

    input: str | List[str] = Field(..., description="Text or list of texts to embed")
    model: Optional[str] = Field(None, description="Embedding model to use (defaults to configured model)")

    class Config:
        json_schema_extra = {
            "example": {
                "input": "The quick brown fox jumps over the lazy dog",
                "model": "nomic-embed-text",
            }
        }


class EmbeddingData(BaseModel):
    """Individual embedding result"""

    embedding: List[float] = Field(..., description="The embedding vector")
    index: int = Field(..., description="Index of the text in the input list")


class EmbeddingResponse(BaseModel):
    """Response model for embeddings"""

    model: str = Field(..., description="Model used for embeddings")
    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")
    total_duration: Optional[int] = Field(None, description="Total duration in nanoseconds")


# Chat Models (for more structured conversations)
class ChatMessage(BaseModel):
    """A single message in a chat conversation"""

    role: str = Field(..., description="Role of the message sender (system/user/assistant)")
    content: str = Field(..., description="Content of the message")


class ChatRequest(BaseModel):
    """Request model for chat-based inference"""

    messages: List[ChatMessage] = Field(..., description="List of conversation messages")
    model: Optional[str] = Field(None, description="Model to use (defaults to configured model)")
    stream: bool = Field(False, description="Stream the response")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens to generate")

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
    total_duration: Optional[int] = Field(None, description="Total duration in nanoseconds")
    prompt_eval_count: Optional[int] = Field(None, description="Number of tokens in prompt")
    eval_count: Optional[int] = Field(None, description="Number of tokens generated")


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
    size: Optional[int] = Field(None, description="Model size in bytes")
    modified_at: Optional[str] = Field(None, description="Last modification time")
    digest: Optional[str] = Field(None, description="Model digest/hash")


class ModelsResponse(BaseModel):
    """Response containing list of available models"""

    models: List[ModelInfo] = Field(..., description="List of available models")


# RAG Models
class DocumentIngestRequest(BaseModel):
    """Request model for ingesting documents into RAG system"""

    content: str = Field(..., description="Document content to ingest")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Document metadata")
    collection: Optional[str] = Field(None, description="Collection name (defaults to configured collection)")
    chunk_size: Optional[int] = Field(None, description="Chunk size for splitting (defaults to configured size)")
    chunk_overlap: Optional[int] = Field(None, description="Overlap between chunks (defaults to configured overlap)")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "This is a sample document about AI...",
                "metadata": {"source": "article.pdf", "author": "John Doe", "date": "2025-01-15"},
                "collection": "documents"
            }
        }


class DocumentChunk(BaseModel):
    """A single document chunk"""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    content: str = Field(..., description="Chunk content")
    metadata: Dict[str, Any] = Field(..., description="Chunk metadata")


class DocumentIngestResponse(BaseModel):
    """Response model for document ingestion"""

    collection: str = Field(..., description="Collection name")
    chunks_created: int = Field(..., description="Number of chunks created")
    chunk_ids: List[str] = Field(..., description="List of created chunk IDs")
    embedding_model: str = Field(..., description="Model used for embeddings")


class RAGQueryRequest(BaseModel):
    """Request model for RAG-powered query"""

    query: str = Field(..., description="Query text")
    collection: Optional[str] = Field(None, description="Collection to search (defaults to configured collection)")
    top_k: Optional[int] = Field(None, description="Number of results to retrieve (defaults to configured top_k)")
    model: Optional[str] = Field(None, description="Model for generation (defaults to configured model)")
    system_prompt: Optional[str] = Field(None, description="System prompt for generation")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens to generate")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the benefits of quantum computing?",
                "collection": "documents",
                "top_k": 3,
                "model": "qwen2.5:7b"
            }
        }


class SearchResult(BaseModel):
    """A single search result"""

    chunk_id: str = Field(..., description="Chunk identifier")
    content: str = Field(..., description="Chunk content")
    score: float = Field(..., description="Relevance score")
    metadata: Dict[str, Any] = Field(..., description="Chunk metadata")


class RAGQueryResponse(BaseModel):
    """Response model for RAG-powered query"""

    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    sources: List[SearchResult] = Field(..., description="Source documents used")
    model: str = Field(..., description="Model used for generation")
    collection: str = Field(..., description="Collection searched")


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search"""

    query: str = Field(..., description="Search query")
    collection: Optional[str] = Field(None, description="Collection to search (defaults to configured collection)")
    top_k: Optional[int] = Field(None, description="Number of results to return (defaults to configured top_k)")
    score_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum similarity score")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "machine learning algorithms",
                "collection": "documents",
                "top_k": 5,
                "score_threshold": 0.7
            }
        }


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search"""

    query: str = Field(..., description="Search query")
    results: List[SearchResult] = Field(..., description="Search results")
    collection: str = Field(..., description="Collection searched")
    total_results: int = Field(..., description="Total number of results")


class CollectionInfo(BaseModel):
    """Information about a collection"""

    name: str = Field(..., description="Collection name")
    vectors_count: int = Field(..., description="Number of vectors in collection")
    points_count: int = Field(..., description="Number of points in collection")


class CollectionsResponse(BaseModel):
    """Response containing list of collections"""

    collections: List[CollectionInfo] = Field(..., description="List of collections")


class CollectionDeleteResponse(BaseModel):
    """Response for collection deletion"""

    collection: str = Field(..., description="Deleted collection name")
    success: bool = Field(..., description="Whether deletion was successful")
