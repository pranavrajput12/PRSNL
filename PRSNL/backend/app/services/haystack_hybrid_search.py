"""
Haystack 2.15.2 Hybrid Search Implementation
Combines dense embeddings with sparse keyword search for superior results
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

from haystack import Pipeline, Document
from haystack.components.retrievers import (
    InMemoryEmbeddingRetriever,
    InMemoryBM25Retriever
)
from haystack.components.embedders import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder
)
from haystack.components.joiners import DocumentJoiner
from haystack.components.rankers import TransformersSimilarityRanker
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.writers import DocumentWriter

from app.config import settings
from app.services.performance_monitoring import profile_ai, track_custom_metric
from app.db.database import get_db_connection

logger = logging.getLogger(__name__)


class HybridSearchEngine:
    """
    Advanced hybrid search using Haystack 2.15.2
    Combines BM25 (sparse) and embedding (dense) retrieval
    """
    
    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        reranking_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        self.embedding_model = embedding_model
        self.reranking_model = reranking_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize document store with hybrid capabilities
        self.document_store = InMemoryDocumentStore(
            embedding_similarity_function="cosine",
            bm25_algorithm="BM25Plus"  # Enhanced BM25 algorithm
        )
        
        # Initialize components
        self._setup_indexing_pipeline()
        self._setup_search_pipeline()
        
        # Search statistics
        self.stats = {
            "searches": 0,
            "documents_indexed": 0,
            "avg_retrieval_time": 0,
            "avg_reranking_time": 0
        }
    
    def _setup_indexing_pipeline(self):
        """Setup the document indexing pipeline"""
        # Document splitter for chunking
        self.splitter = DocumentSplitter(
            split_by="word",
            split_length=self.chunk_size,
            split_overlap=self.chunk_overlap,
            split_threshold=0
        )
        
        # Document embedder
        self.doc_embedder = SentenceTransformersDocumentEmbedder(
            model=self.embedding_model,
            batch_size=32,
            progress_bar=True,
            normalize_embeddings=True
        )
        
        # Document writer
        self.writer = DocumentWriter(document_store=self.document_store)
        
        # Create indexing pipeline
        self.indexing_pipeline = Pipeline()
        self.indexing_pipeline.add_component("splitter", self.splitter)
        self.indexing_pipeline.add_component("embedder", self.doc_embedder)
        self.indexing_pipeline.add_component("writer", self.writer)
        
        # Connect components
        self.indexing_pipeline.connect("splitter", "embedder")
        self.indexing_pipeline.connect("embedder", "writer")
    
    def _setup_search_pipeline(self):
        """Setup the hybrid search pipeline"""
        # Query embedder
        self.query_embedder = SentenceTransformersTextEmbedder(
            model=self.embedding_model,
            normalize_embeddings=True
        )
        
        # BM25 retriever (sparse)
        self.bm25_retriever = InMemoryBM25Retriever(
            document_store=self.document_store,
            top_k=20,
            scale_score=True
        )
        
        # Embedding retriever (dense)
        self.embedding_retriever = InMemoryEmbeddingRetriever(
            document_store=self.document_store,
            top_k=20,
            scale_score=True
        )
        
        # Document joiner to combine results
        self.joiner = DocumentJoiner(
            join_mode="reciprocal_rank_fusion",
            weights=[0.5, 0.5],  # Equal weight to BM25 and embeddings
            top_k=20
        )
        
        # Reranker for final ranking
        self.reranker = TransformersSimilarityRanker(
            model=self.reranking_model,
            top_k=10,
            batch_size=16
        )
        
        # Create search pipeline
        self.search_pipeline = Pipeline()
        self.search_pipeline.add_component("query_embedder", self.query_embedder)
        self.search_pipeline.add_component("bm25_retriever", self.bm25_retriever)
        self.search_pipeline.add_component("embedding_retriever", self.embedding_retriever)
        self.search_pipeline.add_component("joiner", self.joiner)
        self.search_pipeline.add_component("reranker", self.reranker)
        
        # Connect components
        self.search_pipeline.connect("query_embedder.embedding", "embedding_retriever.query_embedding")
        self.search_pipeline.connect("bm25_retriever", "joiner")
        self.search_pipeline.connect("embedding_retriever", "joiner")
        self.search_pipeline.connect("joiner", "reranker")
    
    @profile_ai(model="haystack", operation="document_indexing")
    async def index_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Index documents for hybrid search
        
        Args:
            documents: List of document dictionaries with 'content' and 'meta' fields
            batch_size: Batch size for indexing
            
        Returns:
            Indexing results
        """
        try:
            start_time = datetime.utcnow()
            
            # Convert to Haystack documents
            haystack_docs = []
            for doc in documents:
                haystack_doc = Document(
                    content=doc.get("content", ""),
                    meta=doc.get("meta", {})
                )
                haystack_docs.append(haystack_doc)
            
            # Process in batches
            total_chunks = 0
            for i in range(0, len(haystack_docs), batch_size):
                batch = haystack_docs[i:i + batch_size]
                
                # Run indexing pipeline
                result = self.indexing_pipeline.run({
                    "splitter": {"documents": batch}
                })
                
                chunks_created = len(result["writer"]["documents_written"])
                total_chunks += chunks_created
                
                logger.info(f"Indexed batch {i//batch_size + 1}: {chunks_created} chunks created")
            
            # Update statistics
            self.stats["documents_indexed"] += len(documents)
            
            end_time = datetime.utcnow()
            indexing_time = (end_time - start_time).total_seconds()
            
            track_custom_metric("haystack.documents.indexed", len(documents))
            track_custom_metric("haystack.chunks.created", total_chunks)
            
            return {
                "success": True,
                "documents_indexed": len(documents),
                "chunks_created": total_chunks,
                "indexing_time": indexing_time,
                "avg_chunks_per_doc": total_chunks / max(len(documents), 1)
            }
            
        except Exception as e:
            logger.error(f"Document indexing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @profile_ai(model="haystack", operation="hybrid_search")
    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining BM25 and semantic search
        
        Args:
            query: Search query
            filters: Optional metadata filters
            top_k: Number of results to return
            
        Returns:
            Search results with scores
        """
        try:
            start_time = datetime.utcnow()
            
            # Update retrievers with filters
            if filters:
                self.bm25_retriever.filters = filters
                self.embedding_retriever.filters = filters
            
            # Update top_k
            self.reranker.top_k = top_k
            
            # Run search pipeline
            result = self.search_pipeline.run({
                "query_embedder": {"text": query},
                "bm25_retriever": {"query": query},
                "reranker": {"query": query}
            })
            
            # Extract documents from reranker output
            documents = result.get("reranker", {}).get("documents", [])
            
            # Calculate search time
            end_time = datetime.utcnow()
            search_time = (end_time - start_time).total_seconds()
            
            # Update statistics
            self.stats["searches"] += 1
            self.stats["avg_retrieval_time"] = (
                (self.stats["avg_retrieval_time"] * (self.stats["searches"] - 1) + search_time)
                / self.stats["searches"]
            )
            
            track_custom_metric("haystack.searches.completed", 1)
            track_custom_metric("haystack.search.latency", search_time * 1000)
            
            # Format results
            results = []
            for doc in documents:
                results.append({
                    "content": doc.content,
                    "score": doc.score,
                    "meta": doc.meta,
                    "id": doc.id
                })
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_results": len(results),
                "search_time": search_time,
                "search_type": "hybrid",
                "components_used": ["bm25", "embeddings", "reranking"]
            }
            
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            track_custom_metric("haystack.searches.failed", 1)
            
            return {
                "success": False,
                "query": query,
                "error": str(e)
            }
    
    async def explain_search(
        self,
        query: str,
        document_id: str
    ) -> Dict[str, Any]:
        """
        Explain why a document was retrieved for a query
        Shows BM25 and embedding scores separately
        """
        try:
            # Get BM25 score
            bm25_result = self.search_pipeline.run({
                "bm25_retriever": {"query": query}
            })
            
            bm25_docs = bm25_result.get("bm25_retriever", {}).get("documents", [])
            bm25_score = next(
                (doc.score for doc in bm25_docs if doc.id == document_id),
                0.0
            )
            
            # Get embedding score
            embedding_result = self.search_pipeline.run({
                "query_embedder": {"text": query},
                "embedding_retriever": {"query_embedding": None}
            })
            
            embedding_docs = embedding_result.get("embedding_retriever", {}).get("documents", [])
            embedding_score = next(
                (doc.score for doc in embedding_docs if doc.id == document_id),
                0.0
            )
            
            # Calculate combined score (reciprocal rank fusion)
            combined_score = (bm25_score + embedding_score) / 2
            
            return {
                "success": True,
                "document_id": document_id,
                "scores": {
                    "bm25": float(bm25_score),
                    "embedding": float(embedding_score),
                    "combined": float(combined_score)
                },
                "explanation": {
                    "bm25": "Keyword matching score based on term frequency",
                    "embedding": "Semantic similarity score based on meaning",
                    "combined": "Hybrid score using reciprocal rank fusion"
                }
            }
            
        except Exception as e:
            logger.error(f"Search explanation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        return {
            "total_documents": self.document_store.count_documents(),
            "searches_performed": self.stats["searches"],
            "documents_indexed": self.stats["documents_indexed"],
            "average_search_time": self.stats["avg_retrieval_time"],
            "embedding_model": self.embedding_model,
            "reranking_model": self.reranking_model,
            "search_type": "hybrid",
            "features": [
                "bm25_sparse_retrieval",
                "dense_embedding_retrieval",
                "reciprocal_rank_fusion",
                "transformer_reranking"
            ]
        }
    
    async def update_document(
        self,
        document_id: str,
        content: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update a document in the index"""
        try:
            # Get existing document
            existing_docs = self.document_store.filter_documents(
                filters={"id": document_id}
            )
            
            if not existing_docs:
                logger.warning(f"Document {document_id} not found for update")
                return False
            
            # Update document
            doc = existing_docs[0]
            if content:
                doc.content = content
            if meta:
                doc.meta.update(meta)
            
            # Re-embed if content changed
            if content:
                result = self.doc_embedder.run(documents=[doc])
                doc = result["documents"][0]
            
            # Update in store
            self.document_store.write_documents([doc], policy="overwrite")
            
            return True
            
        except Exception as e:
            logger.error(f"Document update error: {e}")
            return False
    
    async def delete_documents(
        self,
        document_ids: List[str]
    ) -> int:
        """Delete documents from the index"""
        try:
            deleted = 0
            for doc_id in document_ids:
                self.document_store.delete_documents([doc_id])
                deleted += 1
            
            logger.info(f"Deleted {deleted} documents from index")
            return deleted
            
        except Exception as e:
            logger.error(f"Document deletion error: {e}")
            return 0


# Convenience function
def create_hybrid_search_engine() -> HybridSearchEngine:
    """Create a configured hybrid search engine"""
    return HybridSearchEngine()