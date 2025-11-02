import logging
from typing import List, Dict, Tuple
from sentence_transformers import CrossEncoder
import numpy as np

logger = logging.getLogger(__name__)


class Reranker:
    """Cross-encoder reranker for improving retrieval accuracy"""
    
    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        """
        Initialize reranker with a cross-encoder model
        
        Default model: cross-encoder/ms-marco-MiniLM-L-6-v2
        - Fast and efficient (6 layers)
        - Trained on MS MARCO passage ranking dataset
        - Good balance between speed and accuracy
        """
        logger.info(f"Loading cross-encoder model: {model_name}")
        try:
            self.model = CrossEncoder(model_name, max_length=512)
            logger.info(f"Reranker model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            self.model = None
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        metadata: List[Dict],
        top_k: int = 8
    ) -> Tuple[List[str], List[Dict]]:
        """
        Rerank documents using cross-encoder for better relevance
        
        Args:
            query: User query
            documents: List of retrieved documents
            metadata: List of metadata dicts for each document
            top_k: Number of top results to return
        
        Returns:
            Reranked documents and metadata
        """
        if not self.model:
            logger.warning("Reranker model not available, returning original order")
            return documents[:top_k], metadata[:top_k]
        
        if not documents:
            return [], []
        
        try:
            # Prepare query-document pairs
            pairs = [[query, doc] for doc in documents]
            
            # Get relevance scores from cross-encoder
            scores = self.model.predict(pairs)
            
            # Sort by scores (descending)
            sorted_indices = np.argsort(scores)[::-1]
            
            # Rerank documents and metadata
            reranked_docs = [documents[idx] for idx in sorted_indices[:top_k]]
            reranked_metadata = [metadata[idx].copy() for idx in sorted_indices[:top_k]]
            
            # Add reranker scores to metadata
            for i, idx in enumerate(sorted_indices[:top_k]):
                reranked_metadata[i]['reranker_score'] = float(scores[idx])
                reranked_metadata[i]['original_rank'] = int(idx + 1)
                reranked_metadata[i]['reranked_position'] = i + 1
            
            logger.info(f"Reranked {len(documents)} documents -> top {len(reranked_docs)} results")
            logger.debug(f"Top reranker score: {scores[sorted_indices[0]]:.3f}, Lowest: {scores[sorted_indices[top_k-1]]:.3f}")
            
            return reranked_docs, reranked_metadata
        
        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            # Fallback to original order
            return documents[:top_k], metadata[:top_k]
    
    def compute_dynamic_threshold(self, scores: List[float], percentile: float = 50) -> float:
        """
        Compute dynamic relevance threshold based on score distribution
        
        Args:
            scores: List of relevance scores
            percentile: Percentile to use as threshold (default 50th percentile = median)
        
        Returns:
            Dynamic threshold value
        """
        if not scores:
            return 0.3  # Default fallback
        
        threshold = np.percentile(scores, percentile)
        logger.debug(f"Dynamic threshold at {percentile}th percentile: {threshold:.3f}")
        
        return float(threshold)
    
    def filter_by_confidence(
        self,
        documents: List[str],
        metadata: List[Dict],
        min_score: float = 0.0
    ) -> Tuple[List[str], List[Dict]]:
        """
        Filter documents by reranker confidence score
        
        Args:
            documents: List of documents
            metadata: List of metadata (must contain 'reranker_score')
            min_score: Minimum reranker score to keep
        
        Returns:
            Filtered documents and metadata
        """
        filtered_docs = []
        filtered_meta = []
        
        for doc, meta in zip(documents, metadata):
            score = meta.get('reranker_score', 0.0)
            if score >= min_score:
                filtered_docs.append(doc)
                filtered_meta.append(meta)
        
        logger.info(f"Filtered {len(documents)} documents by min_score={min_score} -> {len(filtered_docs)} kept")
        
        return filtered_docs, filtered_meta
