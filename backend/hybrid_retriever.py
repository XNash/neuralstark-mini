import logging
from typing import List, Dict, Tuple
from rank_bm25 import BM25Okapi
import numpy as np

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Hybrid retrieval combining dense (semantic) and sparse (BM25) search"""
    
    def __init__(self):
        self.bm25_index = None
        self.corpus_texts = []
        self.corpus_metadata = []
        logger.info("Hybrid retriever initialized")
    
    def index_documents(self, texts: List[str], metadata: List[Dict]):
        """Index documents for BM25 sparse retrieval"""
        if not texts:
            logger.warning("No texts provided for BM25 indexing")
            return
        
        self.corpus_texts = texts
        self.corpus_metadata = metadata
        
        # Tokenize documents for BM25
        tokenized_corpus = [doc.lower().split() for doc in texts]
        
        # Create BM25 index
        self.bm25_index = BM25Okapi(tokenized_corpus)
        
        logger.info(f"Indexed {len(texts)} documents for BM25 sparse retrieval")
    
    def search_sparse(self, query: str, n_results: int = 20) -> Tuple[List[str], List[Dict], List[float]]:
        """Perform BM25 sparse search (keyword-based)"""
        if not self.bm25_index or not self.corpus_texts:
            logger.warning("BM25 index is empty")
            return [], [], []
        
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get BM25 scores
        scores = self.bm25_index.get_scores(tokenized_query)
        
        # Get top N results
        n_results = min(n_results, len(scores))
        top_indices = np.argsort(scores)[::-1][:n_results]
        
        # Filter out zero scores
        top_indices = [idx for idx in top_indices if scores[idx] > 0]
        
        # Prepare results
        documents = [self.corpus_texts[idx] for idx in top_indices]
        metadatas = [self.corpus_metadata[idx].copy() for idx in top_indices]
        bm25_scores = [float(scores[idx]) for idx in top_indices]
        
        # Add BM25 scores to metadata
        for meta, score in zip(metadatas, bm25_scores):
            meta['bm25_score'] = score
        
        logger.info(f"BM25 search: found {len(documents)} results with scores > 0")
        return documents, metadatas, bm25_scores
    
    def reciprocal_rank_fusion(
        self,
        dense_docs: List[str],
        dense_metadata: List[Dict],
        sparse_docs: List[str],
        sparse_metadata: List[Dict],
        k: int = 60,
        n_results: int = 20
    ) -> Tuple[List[str], List[Dict]]:
        """
        Combine dense and sparse results using Reciprocal Rank Fusion (RRF)
        
        RRF formula: score(d) = sum(1 / (k + rank(d))) for each ranking
        k is a constant (typically 60) to avoid division by zero and reduce impact of high ranks
        """
        # Create document to metadata mapping
        doc_to_meta = {}
        rrf_scores = {}
        
        # Process dense results
        for rank, (doc, meta) in enumerate(zip(dense_docs, dense_metadata), start=1):
            doc_key = doc[:100]  # Use first 100 chars as key
            if doc_key not in rrf_scores:
                rrf_scores[doc_key] = 0
                doc_to_meta[doc_key] = {'doc': doc, 'meta': meta}
            
            # Add dense ranking contribution
            rrf_scores[doc_key] += 1.0 / (k + rank)
            doc_to_meta[doc_key]['meta']['dense_rank'] = rank
        
        # Process sparse results
        for rank, (doc, meta) in enumerate(zip(sparse_docs, sparse_metadata), start=1):
            doc_key = doc[:100]
            if doc_key not in rrf_scores:
                rrf_scores[doc_key] = 0
                doc_to_meta[doc_key] = {'doc': doc, 'meta': meta}
            
            # Add sparse ranking contribution
            rrf_scores[doc_key] += 1.0 / (k + rank)
            doc_to_meta[doc_key]['meta']['sparse_rank'] = rank
        
        # Sort by RRF score
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Take top N results
        top_docs = sorted_docs[:n_results]
        
        # Prepare final results
        final_docs = []
        final_metadata = []
        
        for doc_key, rrf_score in top_docs:
            doc_data = doc_to_meta[doc_key]
            final_docs.append(doc_data['doc'])
            
            meta = doc_data['meta']
            meta['rrf_score'] = rrf_score
            meta['retrieval_method'] = 'hybrid'
            final_metadata.append(meta)
        
        logger.info(f"RRF fusion: combined {len(dense_docs)} dense + {len(sparse_docs)} sparse -> {len(final_docs)} results")
        
        return final_docs, final_metadata
    
    def get_corpus_stats(self) -> Dict:
        """Get statistics about indexed corpus"""
        return {
            'total_documents': len(self.corpus_texts),
            'indexed': self.bm25_index is not None,
            'avg_doc_length': sum(len(doc.split()) for doc in self.corpus_texts) / len(self.corpus_texts) if self.corpus_texts else 0
        }
