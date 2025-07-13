"""
Haystack v2 RAG Service for PRSNL
Implements advanced Retrieval-Augmented Generation using Haystack v2

Features:
- Document ingestion and preprocessing
- Vector-based semantic search
- Hybrid search (keyword + semantic)
- Multi-modal retrieval
- Answer generation with citations
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from app.config import settings
from app.db.database import get_db_pool

logger = logging.getLogger(__name__)

# Try to import Haystack components
try:
    import os
    os.environ['SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL'] = 'True'
    
    from haystack import Document, Pipeline
    from haystack.components.builders import AnswerBuilder, PromptBuilder
    from haystack.components.embedders import (
        SentenceTransformersDocumentEmbedder,
        SentenceTransformersTextEmbedder,
    )
    from haystack.components.generators import AzureOpenAIGenerator, OpenAIGenerator
    from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
    from haystack.components.retrievers import InMemoryEmbeddingRetriever
    from haystack.components.writers import DocumentWriter
    from haystack.document_stores.in_memory import InMemoryDocumentStore
    from haystack.utils import Secret
    from haystack_integrations.components.retrievers.pgvector import (
        PgvectorEmbeddingRetriever,
    )
    from haystack_integrations.document_stores.pgvector import PgvectorDocumentStore
    
    HAYSTACK_AVAILABLE = True
    logger.info("Haystack v2 successfully imported")
    
except ImportError as e:
    logger.error(f"Haystack import failed: {e}")
    HAYSTACK_AVAILABLE = False
except ValueError as e:
    # Handle numpy/sklearn incompatibility
    logger.error(f"Haystack initialization failed due to numpy/sklearn incompatibility: {e}")
    HAYSTACK_AVAILABLE = False
    
    # Create dummy classes to prevent runtime errors
    class Pipeline:
        pass
    
    class Document:
        pass
    
    class Secret:
        @staticmethod
        def from_token(token):
            return token
        @staticmethod
        def from_env_var(var):
            return None
    
    class DocumentCleaner:
        pass
    
    class DocumentSplitter:
        pass
    
    class SentenceTransformersDocumentEmbedder:
        pass
    
    class SentenceTransformersTextEmbedder:
        pass
    
    class PromptBuilder:
        pass
    
    class AnswerBuilder:
        pass
    
    class OpenAIGenerator:
        pass
    
    class AzureOpenAIGenerator:
        pass
    
    class InMemoryEmbeddingRetriever:
        pass
    
    class InMemoryDocumentStore:
        pass
    
    class DocumentWriter:
        pass
    
    class PgvectorDocumentStore:
        pass
    
    class PgvectorEmbeddingRetriever:
        pass


class HaystackRAGService:
    """Advanced RAG implementation using Haystack v2"""
    
    def __init__(self):
        self.enabled = bool(settings.AZURE_OPENAI_API_KEY)
        self.document_store = None
        self.indexing_pipeline = None
        self.query_pipeline = None
        self.hybrid_pipeline = None
        
        if self.enabled:
            self._initialize_components()
        else:
            logger.warning("Haystack RAG service disabled. Azure OpenAI API key required.")
    
    def _initialize_components(self):
        """Initialize Haystack components and pipelines"""
        try:
            # Initialize document store with PostgreSQL + pgvector
            if settings.DATABASE_URL:
                self.document_store = self._create_pgvector_store()
            else:
                # Fallback to in-memory store for development
                self.document_store = InMemoryDocumentStore(
                    embedding_similarity_function="cosine",
                    duplicate_documents="skip"
                )
            
            # Create pipelines
            self.indexing_pipeline = self._create_indexing_pipeline()
            self.query_pipeline = self._create_query_pipeline()
            self.hybrid_pipeline = self._create_hybrid_search_pipeline()
            
            logger.info("Haystack RAG service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Haystack components: {e}")
            self.enabled = False
    
    def _create_pgvector_store(self) -> Optional[PgvectorDocumentStore]:
        """Create PGVector document store for production"""
        try:
            # Try environment variable first (more secure)
            import os
            if os.environ.get("PG_CONN_STR"):
                # Use default which reads from PG_CONN_STR environment variable
                connection_secret = Secret.from_env_var("PG_CONN_STR")
            else:
                # Fallback to using DATABASE_URL with Secret.from_token
                connection_secret = Secret.from_token(settings.DATABASE_URL)
            
            return PgvectorDocumentStore(
                connection_string=connection_secret,
                table_name="haystack_documents",
                embedding_dimension=384,  # all-MiniLM-L6-v2 dimension
                recreate_table=False
            )
        except Exception as e:
            logger.error(f"Failed to create PGVector store: {e}")
            return None
    
    def _create_indexing_pipeline(self) -> Pipeline:
        """Create document indexing pipeline"""
        indexing_pipeline = Pipeline()
        
        # Add document cleaner
        cleaner = DocumentCleaner(
            remove_empty_lines=True,
            remove_extra_whitespaces=True,
            remove_repeated_substrings=True
        )
        indexing_pipeline.add_component("cleaner", cleaner)
        
        # Add document splitter
        splitter = DocumentSplitter(
            split_by="sentence",
            split_length=3,
            split_overlap=1,
            split_threshold=0.5
        )
        indexing_pipeline.add_component("splitter", splitter)
        
        # Add embedder
        embedder = SentenceTransformersDocumentEmbedder(
            model="sentence-transformers/all-MiniLM-L6-v2",
            progress_bar=False
        )
        indexing_pipeline.add_component("embedder", embedder)
        
        # Add writer
        writer = DocumentWriter(document_store=self.document_store)
        indexing_pipeline.add_component("writer", writer)
        
        # Connect components
        indexing_pipeline.connect("cleaner", "splitter")
        indexing_pipeline.connect("splitter", "embedder")
        indexing_pipeline.connect("embedder", "writer")
        
        return indexing_pipeline
    
    def _create_query_pipeline(self) -> Pipeline:
        """Create RAG query pipeline"""
        query_pipeline = Pipeline()
        
        # Add text embedder for queries
        text_embedder = SentenceTransformersTextEmbedder(
            model="sentence-transformers/all-MiniLM-L6-v2",
            progress_bar=False
        )
        query_pipeline.add_component("text_embedder", text_embedder)
        
        # Add retriever
        if isinstance(self.document_store, PgvectorDocumentStore):
            retriever = PgvectorEmbeddingRetriever(
                document_store=self.document_store,
                top_k=5
            )
        else:
            retriever = InMemoryEmbeddingRetriever(
                document_store=self.document_store,
                top_k=5
            )
        query_pipeline.add_component("retriever", retriever)
        
        # Add prompt builder
        prompt_template = """
        Answer the question based on the given context.
        If the answer is not in the context, say "I don't have enough information to answer this question."
        
        Context:
        {% for doc in documents %}
        {{ doc.content }}
        {% endfor %}
        
        Question: {{ question }}
        
        Answer:
        """
        
        prompt_builder = PromptBuilder(template=prompt_template)
        query_pipeline.add_component("prompt_builder", prompt_builder)
        
        # Add generator (using Azure OpenAI)
        generator = AzureOpenAIGenerator(
            api_key=Secret.from_token(settings.AZURE_OPENAI_API_KEY),
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            generation_kwargs={
                "temperature": 0.7,
                "max_tokens": 500
            }
        )
        query_pipeline.add_component("generator", generator)
        
        # Add answer builder
        answer_builder = AnswerBuilder()
        query_pipeline.add_component("answer_builder", answer_builder)
        
        # Connect components
        query_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
        query_pipeline.connect("retriever.documents", "prompt_builder.documents")
        query_pipeline.connect("prompt_builder.prompt", "generator.prompt")
        query_pipeline.connect("generator.replies", "answer_builder.replies")
        query_pipeline.connect("retriever.documents", "answer_builder.documents")
        
        return query_pipeline
    
    def _create_hybrid_search_pipeline(self) -> Pipeline:
        """Create hybrid search pipeline combining keyword and semantic search"""
        # This will be implemented in the next iteration
        # For now, return the query pipeline
        return self.query_pipeline
    
    async def ingest_document(self, 
                            content: str, 
                            metadata: Dict[str, Any] = None,
                            doc_id: Optional[str] = None) -> bool:
        """Ingest a document into the RAG system"""
        if not self.enabled:
            logger.warning("RAG service not enabled")
            return False
        
        try:
            # Create document
            document = Document(
                content=content,
                meta=metadata or {},
                id=doc_id or None
            )
            
            # Run indexing pipeline
            result = await asyncio.to_thread(
                self.indexing_pipeline.run,
                {"cleaner": {"documents": [document]}}
            )
            
            logger.info(f"Document ingested successfully: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to ingest document: {e}")
            return False
    
    async def ingest_batch(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ingest multiple documents in batch"""
        if not self.enabled:
            return {"success": 0, "failed": len(documents), "errors": ["Service not enabled"]}
        
        success_count = 0
        failed_count = 0
        errors = []
        
        # Create Document objects
        doc_objects = []
        for doc in documents:
            try:
                doc_obj = Document(
                    content=doc.get("content", ""),
                    meta=doc.get("metadata", {}),
                    id=doc.get("id")
                )
                doc_objects.append(doc_obj)
            except Exception as e:
                failed_count += 1
                errors.append(f"Failed to create document: {e}")
        
        # Run batch indexing
        if doc_objects:
            try:
                result = await asyncio.to_thread(
                    self.indexing_pipeline.run,
                    {"cleaner": {"documents": doc_objects}}
                )
                success_count = len(doc_objects)
            except Exception as e:
                failed_count += len(doc_objects)
                errors.append(f"Batch indexing failed: {e}")
        
        return {
            "success": success_count,
            "failed": failed_count,
            "errors": errors
        }
    
    async def query(self, 
                   question: str,
                   filters: Optional[Dict[str, Any]] = None,
                   top_k: int = 5) -> Dict[str, Any]:
        """Query the RAG system"""
        if not self.enabled:
            return {
                "answer": "RAG service is not available",
                "documents": [],
                "confidence": 0.0
            }
        
        try:
            # Run query pipeline
            result = await asyncio.to_thread(
                self.query_pipeline.run,
                {
                    "text_embedder": {"text": question},
                    "prompt_builder": {"question": question},
                    "answer_builder": {"query": question}
                }
            )
            
            # Extract answer and documents
            answers = result.get("answer_builder", {}).get("answers", [])
            documents = result.get("retriever", {}).get("documents", [])
            
            # Handle GeneratedAnswer objects properly
            answer_text = "No answer found"
            confidence = 0.0
            
            if answers:
                answer_obj = answers[0]
                if hasattr(answer_obj, 'data'):
                    answer_text = answer_obj.data
                elif hasattr(answer_obj, 'answer'):
                    answer_text = answer_obj.answer
                else:
                    answer_text = str(answer_obj)
                
                if hasattr(answer_obj, 'score'):
                    confidence = answer_obj.score
            
            return {
                "answer": answer_text,
                "documents": [
                    {
                        "content": doc.content[:200] + "...",
                        "metadata": doc.meta,
                        "score": doc.score if hasattr(doc, 'score') else 0.0
                    }
                    for doc in documents
                ],
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                "answer": f"Query failed: {str(e)}",
                "documents": [],
                "confidence": 0.0
            }
    
    async def hybrid_search(self,
                          query: str,
                          keyword_weight: float = 0.5,
                          semantic_weight: float = 0.5,
                          top_k: int = 10) -> List[Dict[str, Any]]:
        """Perform hybrid search combining keyword and semantic search"""
        # To be implemented with BM25 + semantic search
        # For now, use semantic search only
        try:
            embedder = SentenceTransformersTextEmbedder(
                model="sentence-transformers/all-MiniLM-L6-v2"
            )
            embedding = await asyncio.to_thread(embedder.run, {"text": query})
            
            if isinstance(self.document_store, PgvectorDocumentStore):
                retriever = PgvectorEmbeddingRetriever(
                    document_store=self.document_store,
                    top_k=top_k
                )
            else:
                retriever = InMemoryEmbeddingRetriever(
                    document_store=self.document_store,
                    top_k=top_k
                )
            
            result = await asyncio.to_thread(
                retriever.run,
                {"query_embedding": embedding["embedding"]}
            )
            
            documents = result.get("documents", [])
            return [
                {
                    "id": doc.id,
                    "content": doc.content,
                    "metadata": doc.meta,
                    "score": doc.score
                }
                for doc in documents
            ]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []
    
    async def update_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """Update an existing document"""
        if not self.enabled:
            return False
        
        try:
            # Delete old document
            self.document_store.delete_documents([doc_id])
            
            # Ingest updated document
            return await self.ingest_document(content, metadata, doc_id)
            
        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            return False
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the RAG system"""
        if not self.enabled:
            return False
        
        try:
            self.document_store.delete_documents([doc_id])
            logger.info(f"Document deleted: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False
    
    async def get_document_count(self) -> int:
        """Get total number of documents in the store"""
        if not self.enabled:
            return 0
        
        try:
            return await asyncio.to_thread(self.document_store.count_documents)
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return 0
    
    async def export_knowledge_base(self, format: str = "json") -> Union[str, Dict[str, Any]]:
        """Export the entire knowledge base"""
        if not self.enabled:
            return {"error": "Service not enabled"}
        
        try:
            # Get all documents
            all_docs = await asyncio.to_thread(
                self.document_store.filter_documents
            )
            
            if format == "json":
                return {
                    "documents": [
                        {
                            "id": doc.id,
                            "content": doc.content,
                            "metadata": doc.meta
                        }
                        for doc in all_docs
                    ],
                    "count": len(all_docs),
                    "exported_at": datetime.now().isoformat()
                }
            else:
                # Add support for other formats (CSV, etc.) later
                return {"error": f"Unsupported format: {format}"}
                
        except Exception as e:
            logger.error(f"Failed to export knowledge base: {e}")
            return {"error": str(e)}


# Singleton instance
haystack_rag_service = HaystackRAGService()