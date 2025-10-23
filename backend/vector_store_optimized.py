import logging
from typing import List, Dict, Tuple
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
import config_paths

logger = logging.getLogger(__name__)


class OptimizedVectorStoreService:
    """Optimized vector store service with batch operations and better performance"""
    
    def __init__(self, collection_name: str = "documents"):
        # Initialize ChromaDB with persistent storage using dynamic paths
        logger.info(f"Using ChromaDB path: {config_paths.CHROMA_DIR_STR}")
        
        self.client = chromadb.PersistentClient(
            path=config_paths.CHROMA_DIR_STR,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model (BAAI for multilingual support)
        logger.info("Loading embedding model: BAAI/bge-base-en-v1.5")
        self.embedding_model = SentenceTransformer('BAAI/bge-base-en-v1.5')
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "RAG document embeddings"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def add_documents_batch(self, texts: List[str], metadata: List[Dict], batch_size: int = 100) -> List[str]:
        """Add documents to vector store in optimized batches
        
        Returns:
            List of document IDs that were added
        """
        if not texts:
            return []
        
        try:
            import time
            timestamp = int(time.time() * 1000)
            
            # Generate all IDs upfront
            all_ids = [f"doc_{timestamp}_{i}_{abs(hash(text)) % 10**8}" for i, text in enumerate(texts)]
            
            # Process in batches for better performance
            total_added = 0
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                batch_metadata = metadata[i:i+batch_size]
                batch_ids = all_ids[i:i+batch_size]
                
                # Generate embeddings for this batch with optimized settings
                batch_embeddings = self.embedding_model.encode(
                    batch_texts,
                    show_progress_bar=False,
                    batch_size=64,  # Larger batch size for embedding model
                    normalize_embeddings=True,
                    convert_to_numpy=True
                )
                
                # Add batch to collection
                self.collection.add(
                    embeddings=batch_embeddings.tolist(),
                    documents=batch_texts,
                    metadatas=batch_metadata,
                    ids=batch_ids
                )
                
                total_added += len(batch_texts)
                logger.debug(f"Added batch {i//batch_size + 1}: {len(batch_texts)} documents")
            
            logger.info(f"Successfully added {total_added} documents to vector store in {(len(texts) + batch_size - 1) // batch_size} batches")
            return all_ids
        
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}", exc_info=True)
            raise
    
    def add_documents(self, texts: List[str], metadata: List[Dict]):
        """Add documents to the vector store (legacy method, uses batch internally)"""
        self.add_documents_batch(texts, metadata)
    
    def search(self, query: str, n_results: int = 5) -> Tuple[List[str], List[Dict]]:
        """Search for relevant documents with enhanced relevance scoring"""
        try:
            # Check if collection has documents
            count = self.collection.count()
            if count == 0:
                logger.warning("Vector store is empty - no documents to search")
                return [], []
            
            # Ensure n_results doesn't exceed available documents
            n_results = min(n_results, count)
            
            # Generate query embedding with normalization
            query_embedding = self.embedding_model.encode(
                [query],
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True
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
            for i, metadata in enumerate(metadatas):
                if i < len(distances):
                    distance = distances[i]
                    # Convert L2 distance to similarity score
                    relevance_score = max(0.0, min(1.0, 1.0 / (1.0 + distance)))
                    metadata['relevance_score'] = relevance_score
                    metadata['distance'] = distance
                else:
                    metadata['relevance_score'] = 0.0
                    metadata['distance'] = float('inf')
            
            # Sort by relevance score
            sorted_results = sorted(
                zip(documents, metadatas),
                key=lambda x: x[1]['relevance_score'],
                reverse=True
            )
            
            if sorted_results:
                documents, metadatas = zip(*sorted_results)
                documents = list(documents)
                metadatas = list(metadatas)
            
            logger.debug(f"Found {len(documents)} relevant documents")
            
            return documents, metadatas
        
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return [], []
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        try:
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
        except:
            return 0
    
    def remove_documents_by_ids(self, ids: List[str]):
        """Remove specific documents by their IDs"""
        try:
            if ids:
                self.collection.delete(ids=ids)
                logger.info(f"Removed {len(ids)} documents from vector store")
        except Exception as e:
            logger.error(f"Error removing documents: {e}")
