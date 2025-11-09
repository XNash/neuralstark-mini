import logging
import hashlib
import pickle
from typing import Optional, Any
from functools import lru_cache
import numpy as np
from collections import OrderedDict
import threading

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """LRU cache for query embeddings to speed up repeated queries"""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize embedding cache with LRU eviction
        
        Args:
            max_size: Maximum number of cached embeddings
        """
        self.max_size = max_size
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.lock = threading.Lock()
        
        logger.info(f"Embedding cache initialized with max_size={max_size}")
    
    def _compute_key(self, query: str, model_name: str = "default") -> str:
        """Compute cache key for query and model"""
        # Use hash of query + model for key
        content = f"{query}:{model_name}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def get(self, query: str, model_name: str = "default") -> Optional[np.ndarray]:
        """
        Get cached embedding for query
        
        Returns:
            Cached embedding or None if not found
        """
        key = self._compute_key(query, model_name)
        
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                logger.debug(f"Cache HIT for query: {query[:50]}...")
                return self.cache[key]
            else:
                self.misses += 1
                logger.debug(f"Cache MISS for query: {query[:50]}...")
                return None
    
    def put(self, query: str, embedding: np.ndarray, model_name: str = "default"):
        """
        Store embedding in cache
        
        Args:
            query: Query text
            embedding: Query embedding
            model_name: Model identifier
        """
        key = self._compute_key(query, model_name)
        
        with self.lock:
            # Remove oldest if at capacity
            if len(self.cache) >= self.max_size:
                # Pop oldest (first item)
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                logger.debug(f"Cache full, evicted oldest entry")
            
            # Add new entry
            self.cache[key] = embedding
            logger.debug(f"Cached embedding for query: {query[:50]}...")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'total_requests': total_requests
        }
    
    def clear(self):
        """Clear all cached embeddings"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
            logger.info("Embedding cache cleared")


class QueryCache:
    """Cache for full query results (documents + metadata)"""
    
    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        """
        Initialize query result cache
        
        Args:
            max_size: Maximum number of cached queries
            ttl_seconds: Time-to-live for cache entries (1 hour default)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        self.timestamps = {}
        self.hits = 0
        self.misses = 0
        self.lock = threading.Lock()
        
        logger.info(f"Query cache initialized with max_size={max_size}, ttl={ttl_seconds}s")
    
    def _compute_key(self, query: str, n_results: int, use_hybrid: bool) -> str:
        """Compute cache key for query parameters"""
        content = f"{query}:{n_results}:{use_hybrid}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        import time
        if key not in self.timestamps:
            return True
        
        age = time.time() - self.timestamps[key]
        return age > self.ttl_seconds
    
    def get(self, query: str, n_results: int, use_hybrid: bool) -> Optional[Any]:
        """
        Get cached query results
        
        Returns:
            Cached (documents, metadata) tuple or None
        """
        key = self._compute_key(query, n_results, use_hybrid)
        
        with self.lock:
            if key in self.cache and not self._is_expired(key):
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                logger.debug(f"Query cache HIT: {query[:50]}...")
                return self.cache[key]
            elif key in self.cache:
                # Expired entry, remove it
                del self.cache[key]
                del self.timestamps[key]
                self.misses += 1
                return None
            else:
                self.misses += 1
                return None
    
    def put(self, query: str, n_results: int, use_hybrid: bool, result: Any):
        """
        Store query results in cache
        
        Args:
            query: Query text
            n_results: Number of results
            use_hybrid: Hybrid search flag
            result: (documents, metadata) tuple to cache
        """
        import time
        key = self._compute_key(query, n_results, use_hybrid)
        
        with self.lock:
            # Remove oldest if at capacity
            if len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
            
            # Add new entry
            self.cache[key] = result
            self.timestamps[key] = time.time()
            logger.debug(f"Query cached: {query[:50]}...")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'total_requests': total_requests,
            'ttl_seconds': self.ttl_seconds
        }
    
    def clear(self):
        """Clear all cached queries"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
            self.hits = 0
            self.misses = 0
            logger.info("Query cache cleared")