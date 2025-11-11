"""RAG (Retrieval-Augmented Generation) endpoints"""

import httpx
import uuid
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List

from app.auth import RequireAPIKey
from app.config import settings
from app.models import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SearchResult,
    CollectionsResponse,
    CollectionInfo,
    CollectionDeleteResponse,
)
from app.utils.text_chunker import TextChunker
from app.utils.qdrant_client import QdrantVectorStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])

# Global Qdrant client (initialized on first use)
_qdrant_client = None


def get_qdrant_client() -> QdrantVectorStore:
    """Get or create Qdrant client instance"""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantVectorStore(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key if settings.qdrant_api_key else None
        )
    return _qdrant_client


async def generate_embeddings(texts: List[str], model: str) -> List[List[float]]:
    """
    Generate embeddings using Ollama

    Args:
        texts: List of texts to embed
        model: Model to use for embeddings

    Returns:
        List of embedding vectors
    """
    embeddings = []

    async with httpx.AsyncClient(timeout=120.0) as client:
        for text in texts:
            payload = {
                "model": model,
                "prompt": text,
            }

            try:
                response = await client.post(
                    f"{settings.ollama_base_url}/api/embeddings",
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
                embeddings.append(result["embedding"])
            except Exception as e:
                logger.error(f"Failed to generate embedding: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate embeddings: {str(e)}"
                )

    return embeddings


@router.post("/ingest", response_model=DocumentIngestResponse)
async def ingest_document(
    request: DocumentIngestRequest,
    api_key: RequireAPIKey,
):
    """
    Ingest a document into the RAG system.

    This endpoint:
    1. Splits the document into chunks
    2. Generates embeddings for each chunk
    3. Stores chunks and embeddings in Qdrant

    Use this to build a searchable knowledge base from your documents.
    """
    collection = request.collection or settings.default_collection
    chunk_size = request.chunk_size or settings.chunk_size
    chunk_overlap = request.chunk_overlap or settings.chunk_overlap
    embedding_model = settings.default_embedding_model

    try:
        # Get Qdrant client
        qdrant = get_qdrant_client()

        # Check if collection exists, create if not
        if not qdrant.collection_exists(collection):
            logger.info(f"Creating new collection: {collection}")
            # We need to know the embedding dimension
            # Generate a test embedding to get the size
            test_embeddings = await generate_embeddings(["test"], embedding_model)
            vector_size = len(test_embeddings[0])

            qdrant.create_collection(
                collection_name=collection,
                vector_size=vector_size
            )

        # Chunk the document
        chunks_with_metadata = TextChunker.chunk_with_metadata(
            text=request.content,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            strategy="recursive"
        )

        if not chunks_with_metadata:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No chunks generated from document"
            )

        # Extract chunk texts
        chunk_texts = [chunk["content"] for chunk in chunks_with_metadata]

        # Generate embeddings for all chunks
        logger.info(f"Generating embeddings for {len(chunk_texts)} chunks")
        embeddings = await generate_embeddings(chunk_texts, embedding_model)

        # Prepare metadata for each chunk
        chunk_metadata = []
        chunk_ids = []
        for chunk_info in chunks_with_metadata:
            chunk_id = str(uuid.uuid4())
            chunk_ids.append(chunk_id)

            metadata = {
                **request.metadata,
                "chunk_index": chunk_info["index"],
                "char_start": chunk_info["char_start"],
                "char_end": chunk_info["char_end"],
                "chunk_length": chunk_info["length"],
            }
            chunk_metadata.append(metadata)

        # Store in Qdrant
        logger.info(f"Storing {len(chunk_texts)} chunks in collection {collection}")
        qdrant.add_documents(
            collection_name=collection,
            documents=chunk_texts,
            embeddings=embeddings,
            metadata=chunk_metadata,
            ids=chunk_ids
        )

        return DocumentIngestResponse(
            collection=collection,
            chunks_created=len(chunk_texts),
            chunk_ids=chunk_ids,
            embedding_model=embedding_model
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(e)}"
        )


@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    api_key: RequireAPIKey,
):
    """
    Perform semantic search across documents.

    This endpoint:
    1. Converts the query to an embedding
    2. Searches for similar chunks in Qdrant
    3. Returns the most relevant results

    Use this to find relevant information without LLM generation.
    """
    collection = request.collection or settings.default_collection
    top_k = request.top_k or settings.top_k_results
    embedding_model = settings.default_embedding_model

    try:
        # Get Qdrant client
        qdrant = get_qdrant_client()

        # Check collection exists
        if not qdrant.collection_exists(collection):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{collection}' not found"
            )

        # Generate query embedding
        logger.info(f"Generating embedding for query")
        query_embeddings = await generate_embeddings([request.query], embedding_model)
        query_vector = query_embeddings[0]

        # Search in Qdrant
        logger.info(f"Searching in collection {collection}")
        results = qdrant.search(
            collection_name=collection,
            query_vector=query_vector,
            top_k=top_k,
            score_threshold=request.score_threshold
        )

        # Format results
        search_results = [
            SearchResult(
                chunk_id=result["id"],
                content=result["text"],
                score=result["score"],
                metadata=result["metadata"]
            )
            for result in results
        ]

        return SemanticSearchResponse(
            query=request.query,
            results=search_results,
            collection=collection,
            total_results=len(search_results)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(
    request: RAGQueryRequest,
    api_key: RequireAPIKey,
):
    """
    Query documents with RAG (Retrieval-Augmented Generation).

    This endpoint:
    1. Searches for relevant document chunks
    2. Constructs a prompt with the retrieved context
    3. Generates an answer using an LLM

    Use this to get AI-powered answers based on your documents.
    """
    collection = request.collection or settings.default_collection
    top_k = request.top_k or settings.top_k_results
    model = request.model or settings.default_inference_model
    embedding_model = settings.default_embedding_model

    try:
        # Get Qdrant client
        qdrant = get_qdrant_client()

        # Check collection exists
        if not qdrant.collection_exists(collection):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{collection}' not found"
            )

        # Step 1: Search for relevant chunks
        logger.info(f"Searching for relevant chunks")
        query_embeddings = await generate_embeddings([request.query], embedding_model)
        query_vector = query_embeddings[0]

        results = qdrant.search(
            collection_name=collection,
            query_vector=query_vector,
            top_k=top_k
        )

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No relevant documents found"
            )

        # Step 2: Build context from retrieved chunks
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Source {i}]\n{result['text']}")

        context = "\n\n".join(context_parts)

        # Step 3: Build prompt
        system_prompt = request.system_prompt or (
            "You are a helpful assistant that answers questions based on the provided context. "
            "Use only the information from the context to answer the question. "
            "If the context doesn't contain enough information to answer the question, say so."
        )

        user_prompt = f"""Context:
{context}

Question: {request.query}

Answer based on the context above:"""

        # Step 4: Generate answer using Ollama
        logger.info(f"Generating answer with model {model}")
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": model,
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                }
            }

            if request.max_tokens:
                payload["options"]["num_predict"] = request.max_tokens

            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            answer = result.get("response", "")

        # Format search results for response
        search_results = [
            SearchResult(
                chunk_id=result["id"],
                content=result["text"],
                score=result["score"],
                metadata=result["metadata"]
            )
            for result in results
        ]

        return RAGQueryResponse(
            query=request.query,
            answer=answer,
            sources=search_results,
            model=model,
            collection=collection
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.get("/collections", response_model=CollectionsResponse)
async def list_collections(
    api_key: RequireAPIKey,
):
    """
    List all document collections.

    Returns information about all collections in the Qdrant database,
    including the number of documents stored in each.
    """
    try:
        qdrant = get_qdrant_client()
        collections = qdrant.list_collections()

        collection_infos = [
            CollectionInfo(
                name=col["name"],
                vectors_count=col["vectors_count"],
                points_count=col["points_count"]
            )
            for col in collections
        ]

        return CollectionsResponse(collections=collection_infos)

    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {str(e)}"
        )


@router.delete("/collections/{collection_name}", response_model=CollectionDeleteResponse)
async def delete_collection(
    collection_name: str,
    api_key: RequireAPIKey,
):
    """
    Delete a document collection.

    WARNING: This permanently deletes all documents in the collection.
    """
    try:
        qdrant = get_qdrant_client()

        # Check if collection exists
        if not qdrant.collection_exists(collection_name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{collection_name}' not found"
            )

        # Delete collection
        success = qdrant.delete_collection(collection_name)

        return CollectionDeleteResponse(
            collection=collection_name,
            success=success
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete collection: {str(e)}"
        )
