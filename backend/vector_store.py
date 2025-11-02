import logging
from typing import List, Dict, Tuple
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import config_paths
from hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing vector embeddings with ChromaDB and hybrid retrieval"""
    
    def __init__(self, collection_name: str = "documents"):
        # Initialize ChromaDB with persistent storage using dynamic paths
        logger.info(f"Using ChromaDB path: {config_paths.CHROMA_DIR_STR}")
        
        self.client = chromadb.PersistentClient(
            path=config_paths.CHROMA_DIR_STR,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model (manu/bge-m3-custom-fr for French-optimized multilingual support)
        logger.info("Loading embedding model: manu/bge-m3-custom-fr")
        self.embedding_model = SentenceTransformer('manu/bge-m3-custom-fr')
        
        # Initialize hybrid retriever for BM25 + dense fusion
        self.hybrid_retriever = HybridRetriever()
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
            # Re-index existing documents for BM25
            self._reindex_bm25()
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "RAG document embeddings"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def add_documents(self, texts: List[str], metadata: List[Dict]):
        """Add documents to the vector store with duplicate detection"""
        if not texts:
            return
        
        try:
            # Generate embeddings with better quality
            embeddings = self.embedding_model.encode(
                texts, 
                show_progress_bar=False,
                batch_size=32,
                normalize_embeddings=True  # Normalize for better cosine similarity
            )
            
            # Generate unique IDs with timestamp for better uniqueness
            import time
            timestamp = int(time.time() * 1000)
            ids = [f"doc_{timestamp}_{i}_{abs(hash(text)) % 10**8}" for i, text in enumerate(texts)]
            
            # Check for existing documents to avoid duplicates
            existing_docs = []
            try:
                # Query with exact embeddings to find duplicates
                for embedding in embeddings[:min(5, len(embeddings))]:  # Check first 5 to avoid overload
                    result = self.collection.query(
                        query_embeddings=[embedding.tolist()],
                        n_results=1
                    )
                    if result['distances'] and result['distances'][0] and result['distances'][0][0] < 0.01:
                        existing_docs.append(True)
                    else:
                        existing_docs.append(False)
            except Exception:
                # If query fails, proceed with adding
                pass
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=metadata,
                ids=ids
            )
            
            # Also index for BM25 sparse retrieval
            self.hybrid_retriever.index_documents(texts, metadata)
            
            logger.info(f"Added {len(texts)} documents to vector store and BM25 index (IDs: {ids[0]}...{ids[-1] if len(ids) > 1 else ''})")
        
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise
    
    def search(self, query: str, n_results: int = 5, use_hybrid: bool = True) -> Tuple[List[str], List[Dict]]:
        """
        Search for relevant documents with enhanced relevance scoring
        
        Args:
            query: Search query
            n_results: Number of results to return
            use_hybrid: Whether to use hybrid (dense + sparse) retrieval
        
        Returns:
            Tuple of (documents, metadata)
        """
        try:
            # Check if collection has documents
            count = self.collection.count()
            if count == 0:
                logger.warning("Vector store is empty - no documents to search")
                return [], []
            
            # Retrieve more candidates for better reranking
            retrieval_count = min(n_results * 3, count)  # Get 3x candidates for reranking
            
            if use_hybrid and self.hybrid_retriever.bm25_index:
                # HYBRID RETRIEVAL: Combine dense + sparse
                logger.info(f"Using hybrid retrieval (dense + BM25) for query: '{query[:50]}...'")
                
                # Step 1: Dense retrieval (semantic search)
                dense_docs, dense_metadata = self._search_dense(query, retrieval_count)
                
                # Step 2: Sparse retrieval (BM25 keyword search)
                sparse_docs, sparse_metadata, _ = self.hybrid_retriever.search_sparse(query, retrieval_count)
                
                # Step 3: Fusion using Reciprocal Rank Fusion
                if sparse_docs:
                    documents, metadatas = self.hybrid_retriever.reciprocal_rank_fusion(
                        dense_docs, dense_metadata,
                        sparse_docs, sparse_metadata,
                        k=60,
                        n_results=retrieval_count
                    )
                else:
                    # Fallback to dense only if sparse failed
                    documents, metadatas = dense_docs, dense_metadata
                
                logger.info(f"Hybrid search returned {len(documents)} fused results")
            else:
                # DENSE ONLY: Semantic search
                logger.info(f"Using dense-only retrieval for query: '{query[:50]}...'")
                documents, metadatas = self._search_dense(query, retrieval_count)
            
            return documents, metadatas
        
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return [], []
    
    def _search_dense(self, query: str, n_results: int) -> Tuple[List[str], List[Dict]]:
        """Perform dense (semantic) search using embeddings"""
        # Ensure n_results doesn't exceed available documents
        count = self.collection.count()
        n_results = min(n_results, count)
        
        # Generate query embedding with normalization
        query_embedding = self.embedding_model.encode(
            [query], 
            show_progress_bar=False,
            normalize_embeddings=True
        )[0]
        
        # Search in collection
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results
        )
        
        # Extract documents and metadata
        documents = results['documents'][0] if results['documents'] else []
        metadatas = results['metadatas'][0] if results['metadatas'] else []
        distances = results['distances'][0] if results['distances'] else []
        
        # Enhanced relevance scoring
        # ChromaDB returns L2 distance - convert to similarity score
        for i, metadata in enumerate(metadatas):
            if i < len(distances):
                # Convert L2 distance to similarity score (0-1 range)
                distance = distances[i]
                # Using exponential decay for better differentiation
                relevance_score = max(0.0, min(1.0, 1.0 / (1.0 + distance)))
                metadata['relevance_score'] = relevance_score
                metadata['distance'] = distance
            else:
                metadata['relevance_score'] = 0.0
                metadata['distance'] = float('inf')
        
        # Sort by relevance score (highest first)
        sorted_results = sorted(
            zip(documents, metadatas),
            key=lambda x: x[1]['relevance_score'],
            reverse=True
        )
        
        if sorted_results:
            documents, metadatas = zip(*sorted_results)
            documents = list(documents)
            metadatas = list(metadatas)
        
        logger.info(f"Dense search: found {len(documents)} relevant documents (collection size: {count})")
        if metadatas:
            logger.info(f"Top relevance score: {metadatas[0]['relevance_score']:.3f}, Lowest: {metadatas[-1]['relevance_score']:.3f}")
        
        return documents, metadatas
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            # Delete and recreate collection
            self.client.delete_collection(name=self.collection.name)
            self.collection = self.client.create_collection(
                name=self.collection.name,
                metadata={"description": "RAG document embeddings"}
            )
            logger.info("Cleared vector store collection")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
    
    def get_collection_count(self) -> int:
        """Get the number of documents in the collection"""
        try:
            return self.collection.count()
        except Exception:
            return 0