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
        """Add documents to the vector store"""
        if not texts:
            return
        
        try:
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
            
            # Generate unique IDs
            ids = [f"doc_{i}_{hash(text)}" for i, text in enumerate(texts)]
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=metadata,
                ids=ids
            )
            
            logger.info(f"Added {len(texts)} documents to vector store")
        
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
    
    def search(self, query: str, n_results: int = 5) -> Tuple[List[str], List[Dict]]:
        """Search for relevant documents"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query], show_progress_bar=False)[0]
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results
            )
            
            # Extract documents and metadata
            documents = results['documents'][0] if results['documents'] else []
            metadatas = results['metadatas'][0] if results['metadatas'] else []
            distances = results['distances'][0] if results['distances'] else []
            
            # Add distance/score to metadata
            for i, metadata in enumerate(metadatas):
                metadata['relevance_score'] = 1 - (distances[i] if i < len(distances) else 1)
            
            logger.info(f"Found {len(documents)} relevant documents for query")
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