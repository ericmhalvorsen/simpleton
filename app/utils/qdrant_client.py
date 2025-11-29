"""Qdrant vector database client for RAG operations"""

import logging
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """Wrapper for Qdrant vector database operations"""

    def __init__(self, url: str, api_key: str | None = None):
        """
        Initialize Qdrant client

        Args:
            url: Qdrant server URL
            api_key: Optional API key for authentication
        """
        self.client = QdrantClient(url=url, api_key=api_key if api_key else None, timeout=60)
        logger.info(f"Initialized Qdrant client connected to {url}")

    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: Distance = Distance.COSINE,
        force_recreate: bool = False,
    ) -> bool:
        """
        Create a new collection in Qdrant

        Args:
            collection_name: Name of the collection
            vector_size: Dimension of vectors
            distance: Distance metric (COSINE, EUCLID, DOT)
            force_recreate: If True, delete existing collection first

        Returns:
            True if successful
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_exists = any(c.name == collection_name for c in collections)

            if collection_exists:
                if force_recreate:
                    logger.info(f"Deleting existing collection: {collection_name}")
                    self.client.delete_collection(collection_name)
                else:
                    logger.info(f"Collection already exists: {collection_name}")
                    return True

            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=distance),
            )
            logger.info(f"Created collection: {collection_name} with vector size {vector_size}")
            return True

        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise

    def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection exists

        Args:
            collection_name: Name of the collection

        Returns:
            True if collection exists
        """
        try:
            collections = self.client.get_collections().collections
            return any(c.name == collection_name for c in collections)
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False

    def get_collection_info(self, collection_name: str) -> dict[str, Any] | None:
        """
        Get information about a collection

        Args:
            collection_name: Name of the collection

        Returns:
            Collection info dict or None if not found
        """
        try:
            collection = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "vectors_count": collection.vectors_count or 0,
                "points_count": collection.points_count or 0,
                "status": collection.status,
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return None

    def list_collections(self) -> list[dict[str, Any]]:
        """
        List all collections

        Returns:
            List of collection info dicts
        """
        try:
            collections = self.client.get_collections().collections
            result = []

            for collection in collections:
                info = self.get_collection_info(collection.name)
                if info:
                    result.append(info)

            return result
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []

    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection

        Args:
            collection_name: Name of the collection

        Returns:
            True if successful
        """
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False

    def add_documents(
        self,
        collection_name: str,
        documents: list[str],
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        """
        Add documents with embeddings to collection

        Args:
            collection_name: Name of the collection
            documents: List of document texts
            embeddings: List of embedding vectors
            metadata: Optional list of metadata dicts
            ids: Optional list of IDs (generated if not provided)

        Returns:
            List of document IDs
        """
        if len(documents) != len(embeddings):
            raise ValueError("Number of documents must match number of embeddings")

        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        # Prepare metadata
        if metadata is None:
            metadata = [{} for _ in documents]
        elif len(metadata) != len(documents):
            raise ValueError("Number of metadata dicts must match number of documents")

        # Create points
        points = []
        for i, (doc_id, doc, embedding, meta) in enumerate(zip(ids, documents, embeddings, metadata)):
            # Add document text to metadata
            payload = {"text": doc, **meta}

            points.append(PointStruct(id=doc_id, vector=embedding, payload=payload))

        # Upload points to Qdrant
        try:
            self.client.upsert(collection_name=collection_name, points=points)
            logger.info(f"Added {len(points)} documents to collection {collection_name}")
            return ids
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        top_k: int = 5,
        score_threshold: float | None = None,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar documents

        Args:
            collection_name: Name of the collection
            query_vector: Query embedding vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            metadata_filter: Optional metadata filter

        Returns:
            List of search results with id, score, text, and metadata
        """
        try:
            # Build filter if provided
            query_filter = None
            if metadata_filter:
                conditions = []
                for key, value in metadata_filter.items():
                    conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
                if conditions:
                    query_filter = Filter(must=conditions)

            # Perform search
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=query_filter,
                score_threshold=score_threshold,
                with_payload=True,
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "id": str(result.id),
                        "score": result.score,
                        "text": result.payload.get("text", ""),
                        "metadata": {k: v for k, v in result.payload.items() if k != "text"},
                    }
                )

            logger.info(f"Search returned {len(formatted_results)} results from {collection_name}")
            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def get_document(self, collection_name: str, document_id: str) -> dict[str, Any] | None:
        """
        Retrieve a specific document by ID

        Args:
            collection_name: Name of the collection
            document_id: Document ID

        Returns:
            Document dict or None if not found
        """
        try:
            result = self.client.retrieve(
                collection_name=collection_name,
                ids=[document_id],
                with_payload=True,
                with_vectors=False,
            )

            if result:
                point = result[0]
                return {
                    "id": str(point.id),
                    "text": point.payload.get("text", ""),
                    "metadata": {k: v for k, v in point.payload.items() if k != "text"},
                }

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve document: {e}")
            return None

    def delete_documents(self, collection_name: str, document_ids: list[str]) -> bool:
        """
        Delete documents by IDs

        Args:
            collection_name: Name of the collection
            document_ids: List of document IDs to delete

        Returns:
            True if successful
        """
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(points=document_ids),
            )
            logger.info(f"Deleted {len(document_ids)} documents from {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False

    def count_documents(self, collection_name: str) -> int:
        """
        Count documents in collection

        Args:
            collection_name: Name of the collection

        Returns:
            Number of documents
        """
        try:
            info = self.client.get_collection(collection_name)
            return info.points_count or 0
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return 0
