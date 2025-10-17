import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class DocumentCache:
    """Cache manager for tracking document processing state"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.document_cache
    
    @staticmethod
    def calculate_file_hash(file_path: Path) -> str:
        """Calculate MD5 hash of file for change detection"""
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b''):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    async def get_cached_document(self, file_path: str) -> Optional[Dict]:
        """Get cached document info"""
        return await self.collection.find_one({"file_path": file_path}, {"_id": 0})
    
    async def is_document_changed(self, file_path: Path) -> bool:
        """Check if document has changed since last processing"""
        try:
            current_hash = self.calculate_file_hash(file_path)
            cached = await self.get_cached_document(str(file_path))
            
            if not cached:
                return True  # New document
            
            # Check if hash or file size changed
            if cached.get('file_hash') != current_hash:
                return True
            
            if cached.get('file_size') != file_path.stat().st_size:
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking document change: {e}")
            return True  # Process on error to be safe
    
    async def update_cache(self, file_path: Path, chunks_count: int, chunk_ids: List[str]):
        """Update cache after successful processing"""
        try:
            file_hash = self.calculate_file_hash(file_path)
            
            cache_entry = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_hash": file_hash,
                "file_size": file_path.stat().st_size,
                "file_type": file_path.suffix.lower(),
                "chunks_count": chunks_count,
                "chunk_ids": chunk_ids,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat()
            }
            
            await self.collection.update_one(
                {"file_path": str(file_path)},
                {"$set": cache_entry},
                upsert=True
            )
            
            logger.debug(f"Updated cache for {file_path.name}")
        except Exception as e:
            logger.error(f"Error updating cache: {e}")
    
    async def remove_cache_entry(self, file_path: str):
        """Remove cache entry for deleted file"""
        await self.collection.delete_one({"file_path": file_path})
    
    async def get_all_cached_files(self) -> List[str]:
        """Get list of all cached file paths"""
        cached_docs = await self.collection.find({}, {"file_path": 1, "_id": 0}).to_list(None)
        return [doc['file_path'] for doc in cached_docs]
    
    async def clear_cache(self):
        """Clear entire cache (for full reindex)"""
        await self.collection.delete_many({})
        logger.info("Document cache cleared")
    
    async def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        total_docs = await self.collection.count_documents({})
        
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_chunks": {"$sum": "$chunks_count"},
                    "total_size": {"$sum": "$file_size"}
                }
            }
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(1)
        
        stats = {
            "total_documents": total_docs,
            "total_chunks": result[0]['total_chunks'] if result else 0,
            "total_size_bytes": result[0]['total_size'] if result else 0
        }
        
        return stats
