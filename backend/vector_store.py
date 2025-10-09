import logging
from typing import List, Dict, Tuple
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing vector embeddings with ChromaDB"""
    
    def __init__(self, collection_name: str = "documents"):
        # Initialize ChromaDB with persistent storage
        self.client = chromadb.Client(Settings(
            persist_directory="/app/backend/chroma_db",
            anonymized_telemetry=False
        ))
        
        # Initialize embedding model (BAAI for multilingual support)
        logger.info("Loading embedding model: BAAI/bge-base-en-v1.5")
        self.embedding_model = SentenceTransformer('BAAI/bge-base-en-v1.5')
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except:
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
            except:
                # If query fails, proceed with adding
                pass
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=metadata,
                ids=ids
            )
            
            logger.info(f"Added {len(texts)} documents to vector store (IDs: {ids[0]}...{ids[-1] if len(ids) > 1 else ''})")
        
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise
    
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
                    # Lower distance = higher similarity
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
            
            logger.info(f"Found {len(documents)} relevant documents for query (collection size: {count})")
            if metadatas:
                logger.info(f"Top relevance score: {metadatas[0]['relevance_score']:.3f}, Lowest: {metadatas[-1]['relevance_score']:.3f}")
            
            return documents, metadatas
        
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return [], []
    
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
        except:
            return 0