# IMPORTANT: Import config_paths FIRST to set environment variables for HuggingFace
import config_paths

from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import document processing and RAG services
from document_processor import DocumentProcessor
from document_processor_optimized import OptimizedDocumentProcessor
from vector_store import VectorStoreService
from vector_store_optimized import OptimizedVectorStoreService
from document_cache import DocumentCache
from rag_service import RAGService
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize services with optimized versions
doc_processor = OptimizedDocumentProcessor()  # Use optimized processor
vector_service = OptimizedVectorStoreService()  # Use optimized vector store
document_cache = DocumentCache(db)  # Initialize cache
rag_service = RAGService(vector_service, db)

# Process pool for parallel document processing
process_pool = None

# Define Models
class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cerebras_api_key: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SettingsUpdate(BaseModel):
    cerebras_api_key: str

class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sources: Optional[List[Dict]] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: List[Dict]

class DocumentStatus(BaseModel):
    total_documents: int
    indexed_documents: int
    last_updated: Optional[str] = None

# File watcher for monitoring /app/files
class DocumentFileHandler(FileSystemEventHandler):
    def __init__(self):
        import threading
        self._lock = threading.Lock()
        self._pending_reindex = False
    
    @property
    def pending_reindex(self):
        with self._lock:
            return self._pending_reindex
    
    @pending_reindex.setter
    def pending_reindex(self, value):
        with self._lock:
            self._pending_reindex = value
        
    def on_created(self, event):
        if not event.is_directory:
            logger.info(f"File created: {event.src_path}")
            self.pending_reindex = True
    
    def on_modified(self, event):
        if not event.is_directory:
            logger.info(f"File modified: {event.src_path}")
            self.pending_reindex = True

async def check_reindex_pending():
    """Background task to check if reindexing is needed"""
    global file_handler
    while True:
        await asyncio.sleep(5)  # Check every 5 seconds
        if file_handler and file_handler.pending_reindex:
            logger.info("Pending reindex detected, processing documents...")
            file_handler.pending_reindex = False
            await process_documents()

# Background task to process documents with OPTIMIZED parallel processing
async def process_documents(clear_existing: bool = False, use_cache: bool = True):
    """Process all documents in files directory with parallel processing and caching
    
    Args:
        clear_existing: If True, clears existing vector store and cache before reindexing
        use_cache: If True, uses cache to skip unchanged documents
    """
    try:
        import time
        start_time = time.time()
        
        # Use dynamic path from config_paths
        files_dir = Path(config_paths.FILES_DIR_STR)
        if not files_dir.exists():
            logger.warning("Files directory does not exist, creating it...")
            files_dir.mkdir(parents=True, exist_ok=True)
            return
        
        supported_extensions = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.odt', '.txt', '.md', '.json', '.csv']
        files = [f for f in files_dir.rglob('*') if f.suffix.lower() in supported_extensions]
        
        logger.info(f"Found {len(files)} documents to process (clear_existing={clear_existing}, use_cache={use_cache})")
        
        if not files:
            logger.warning("No documents found in files directory")
            await db.document_status.update_one(
                {"id": "status"},
                {
                    "$set": {
                        "last_updated": datetime.now(timezone.utc).isoformat(),
                        "total_documents": 0
                    }
                },
                upsert=True
            )
            return
        
        # Clear vector store and cache if requested (for full reindex)
        if clear_existing:
            logger.info("Clearing existing vector store and cache for full reindex...")
            vector_service.clear_collection()
            await document_cache.clear_cache()
            use_cache = False  # Don't use cache after clearing
        
        # Filter files to process based on cache
        files_to_process = []
        skipped_files = []
        
        if use_cache:
            logger.info("Checking cache for unchanged documents...")
            for file_path in files:
                is_changed = await document_cache.is_document_changed(file_path)
                if is_changed:
                    files_to_process.append(file_path)
                else:
                    skipped_files.append(file_path.name)
                    logger.debug(f"Skipping unchanged file: {file_path.name}")
            
            logger.info(f"Cache check complete: {len(files_to_process)} files to process, {len(skipped_files)} files skipped")
        else:
            files_to_process = files
        
        if not files_to_process:
            logger.info("No files need processing (all cached)")
            # Still update status
            await db.document_status.update_one(
                {"id": "status"},
                {
                    "$set": {
                        "last_updated": datetime.now(timezone.utc).isoformat(),
                        "total_documents": len(files)
                    }
                },
                upsert=True
            )
            return
        
        # PARALLEL PROCESSING: Process multiple documents simultaneously
        logger.info(f"Starting parallel processing of {len(files_to_process)} documents...")
        
        # Use asyncio to run document processing in parallel
        loop = asyncio.get_event_loop()
        
        # Process documents in parallel using ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=min(4, len(files_to_process))) as executor:
            # Submit all document processing tasks
            futures = [
                loop.run_in_executor(
                    executor,
                    doc_processor.process_document,
                    str(file_path)
                )
                for file_path in files_to_process
            ]
            
            # Wait for all to complete
            processing_results = await asyncio.gather(*futures, return_exceptions=True)
        
        # Collect all chunks and metadata for batch insertion
        all_chunks = []
        all_metadata = []
        successful_files = 0
        failed_files = []
        file_chunk_map = {}  # Track chunks per file for cache
        
        for file_path, result in zip(files_to_process, processing_results):
            try:
                if isinstance(result, Exception):
                    logger.error(f"✗ Error processing {file_path.name}: {result}")
                    failed_files.append(file_path.name)
                    continue
                
                text_chunks = result
                
                if text_chunks:
                    # Prepare metadata for all chunks
                    file_metadata = [
                        {
                            "source": file_path.name,
                            "chunk_index": i,
                            "total_chunks": len(text_chunks),
                            "file_type": file_path.suffix.lower(),
                            "file_size": file_path.stat().st_size,
                            "processed_at": datetime.now(timezone.utc).isoformat()
                        }
                        for i in range(len(text_chunks))
                    ]
                    
                    # Add to batch
                    chunk_start_idx = len(all_chunks)
                    all_chunks.extend(text_chunks)
                    all_metadata.extend(file_metadata)
                    
                    file_chunk_map[str(file_path)] = {
                        'chunk_count': len(text_chunks),
                        'start_idx': chunk_start_idx
                    }
                    
                    successful_files += 1
                    logger.info(f"✓ Processed {file_path.name}: {len(text_chunks)} chunks")
                else:
                    logger.warning(f"✗ No text extracted from {file_path.name}")
                    failed_files.append(file_path.name)
            except Exception as e:
                logger.error(f"✗ Error handling result for {file_path.name}: {e}", exc_info=True)
                failed_files.append(file_path.name)
        
        # BATCH INSERT: Add all chunks to vector store in one optimized batch operation
        total_chunks = len(all_chunks)
        if total_chunks > 0:
            logger.info(f"Batch inserting {total_chunks} chunks into vector store...")
            batch_start = time.time()
            
            try:
                # Use optimized batch insertion
                chunk_ids = vector_service.add_documents_batch(
                    texts=all_chunks,
                    metadata=all_metadata,
                    batch_size=100  # Process in batches of 100
                )
                
                batch_time = time.time() - batch_start
                logger.info(f"Batch insertion completed in {batch_time:.2f}s ({total_chunks/batch_time:.1f} chunks/sec)")
                
                # Update cache for all successfully processed files
                if use_cache and chunk_ids:
                    for file_path in files_to_process:
                        file_key = str(file_path)
                        if file_key in file_chunk_map:
                            info = file_chunk_map[file_key]
                            start_idx = info['start_idx']
                            chunk_count = info['chunk_count']
                            file_chunk_ids = chunk_ids[start_idx:start_idx+chunk_count]
                            
                            await document_cache.update_cache(
                                file_path,
                                chunk_count,
                                file_chunk_ids
                            )
            except Exception as e:
                logger.error(f"Error in batch insertion: {e}", exc_info=True)
                # Don't fail the entire process, just log the error
        
        # Save updated timestamp to database
        await db.document_status.update_one(
            {"id": "status"},
            {
                "$set": {
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "total_documents": len(files),
                    "successful_files": successful_files + len(skipped_files),  # Include cached files
                    "failed_files": failed_files,
                    "total_chunks": total_chunks,
                    "processing_time_seconds": time.time() - start_time,
                    "files_processed": len(files_to_process),
                    "files_cached": len(skipped_files)
                }
            },
            upsert=True
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"✅ Document processing completed in {elapsed_time:.2f}s:")
        logger.info(f"   - Total files: {len(files)}")
        logger.info(f"   - Processed: {successful_files} files, {total_chunks} chunks")
        logger.info(f"   - Cached: {len(skipped_files)} files")
        logger.info(f"   - Failed: {len(failed_files)} files")
        logger.info(f"   - Speed: {total_chunks/elapsed_time:.1f} chunks/sec" if elapsed_time > 0 else "   - Speed: N/A")
        
        if failed_files:
            logger.warning(f"Failed to process: {', '.join(failed_files)}")
    except Exception as e:
        logger.error(f"Error in process_documents: {e}", exc_info=True)

# API Routes
@api_router.get("/")
async def root():
    return {"message": "NeuralStark API", "status": "running"}

@api_router.get("/health")
async def health_check():
    """Health check endpoint with system status"""
    try:
        # Check MongoDB connection
        try:
            await db.command('ping')
            mongo_status = "connected"
        except Exception as e:
            logger.error(f"MongoDB connection error: {e}")
            mongo_status = "disconnected"
        
        # Get document statistics
        try:
            doc_status = await db.document_status.find_one({"id": "status"}, {"_id": 0})
            documents_indexed = vector_service.get_collection_count()
        except Exception:
            doc_status = None
            documents_indexed = 0
        
        # Calculate uptime (if startup time is tracked)
        import time
        uptime_seconds = int(time.time() - startup_time) if 'startup_time' in globals() else None
        
        return {
            "status": "healthy" if mongo_status == "connected" else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mongodb": mongo_status,
            "documents_indexed": documents_indexed,
            "uptime_seconds": uptime_seconds,
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@api_router.get("/settings", response_model=Settings)
async def get_settings():
    """Get current settings"""
    settings = await db.settings.find_one({"id": "main"}, {"_id": 0})
    if not settings:
        # Return default settings
        return Settings(id="main", cerebras_api_key=None)
    
    if isinstance(settings.get('updated_at'), str):
        settings['updated_at'] = datetime.fromisoformat(settings['updated_at'])
    
    return Settings(**settings)

@api_router.post("/settings", response_model=Settings)
async def update_settings(settings_update: SettingsUpdate):
    """Update settings (API key)"""
    settings_obj = Settings(
        id="main",
        cerebras_api_key=settings_update.cerebras_api_key
    )
    
    doc = settings_obj.model_dump()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.settings.update_one(
        {"id": "main"},
        {"$set": doc},
        upsert=True
    )
    
    # Update RAG service with new API key
    rag_service.update_api_key(settings_update.cerebras_api_key)
    
    return settings_obj

@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with RAG agent with comprehensive error handling"""
    try:
        # Validate input
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if len(request.message) > 10000:
            raise HTTPException(status_code=400, detail="Message too long (max 10,000 characters)")
        
        # Get API key from settings
        settings = await db.settings.find_one({"id": "main"})
        if not settings or not settings.get('gemini_api_key'):
            raise HTTPException(
                status_code=400, 
                detail="Gemini API key not configured. Please add your API key in the Settings page. "
                       "Get one from: https://aistudio.google.com/app/apikey"
            )
        
        # Generate session_id if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get chat history for this session (last 10 messages for context)
        chat_history = await db.chat_messages.find(
            {"session_id": session_id},
            {"_id": 0}
        ).sort("timestamp", 1).to_list(10)
        
        # Save user message
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.message.strip()
        )
        user_doc = user_message.model_dump()
        user_doc['timestamp'] = user_doc['timestamp'].isoformat()
        await db.chat_messages.insert_one(user_doc)
        
        # Get response from RAG service
        try:
            response_text, sources = await rag_service.get_response(
                query=request.message.strip(),
                session_id=session_id,
                api_key=settings['gemini_api_key'],
                chat_history=chat_history
            )
        except Exception as rag_error:
            # Log the error and provide user-friendly message
            error_msg = str(rag_error)
            logger.error(f"RAG service error for session {session_id}: {error_msg}")
            
            # Check for specific error types and provide helpful messages
            if "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
                raise HTTPException(
                    status_code=429,
                    detail="API quota exceeded. The free tier allows 250 requests per day. "
                           "Please check your API key's billing details at https://aistudio.google.com/app/apikey "
                           "or try again later."
                )
            elif "unauthorized" in error_msg.lower() or "invalid" in error_msg.lower():
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key. Please check your Gemini API key in Settings. "
                           "Get a valid key from: https://aistudio.google.com/app/apikey"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to generate response: {error_msg}"
                )
        
        # Save assistant message
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=response_text,
            sources=sources
        )
        assistant_doc = assistant_message.model_dump()
        assistant_doc['timestamp'] = assistant_doc['timestamp'].isoformat()
        await db.chat_messages.insert_one(assistant_doc)
        
        logger.info(f"Successfully processed chat for session {session_id}, found {len(sources)} sources")
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            sources=sources
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.get("/chat/history/{session_id}", response_model=List[ChatMessage])
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    messages = await db.chat_messages.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(100)
    
    for msg in messages:
        if isinstance(msg.get('timestamp'), str):
            msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
    
    return messages

@api_router.get("/documents/status", response_model=DocumentStatus)
async def get_document_status():
    """Get document indexing status"""
    status = await db.document_status.find_one({"id": "status"}, {"_id": 0})
    
    files_dir = Path(config_paths.FILES_DIR_STR)
    supported_extensions = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.odt', '.txt', '.md', '.json', '.csv']
    files = [f for f in files_dir.rglob('*') if f.suffix.lower() in supported_extensions] if files_dir.exists() else []
    
    return DocumentStatus(
        total_documents=len(files),
        indexed_documents=vector_service.get_collection_count(),
        last_updated=status.get('last_updated') if status else None
    )

@api_router.get("/documents/list")
async def list_documents():
    """Get list of all documents categorized by type"""
    try:
        files_dir = Path(config_paths.FILES_DIR_STR)
        
        if not files_dir.exists():
            return {"documents_by_type": {}, "total_count": 0}
        
        # Define file categories
        categories = {
            "PDF": ['.pdf'],
            "Word": ['.docx', '.doc'],
            "Excel": ['.xlsx', '.xls'],
            "Text": ['.txt', '.md'],
            "Data": ['.json', '.csv'],
            "OpenDocument": ['.odt']
        }
        
        # Collect files by category
        documents_by_type = {}
        total_count = 0
        
        for category, extensions in categories.items():
            files = []
            for ext in extensions:
                found_files = list(files_dir.rglob(f'*{ext}'))
                for file_path in found_files:
                    files.append({
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "size_formatted": format_file_size(file_path.stat().st_size),
                        "modified": file_path.stat().st_mtime,
                        "extension": file_path.suffix.lower()
                    })
            
            if files:
                # Sort by name
                files.sort(key=lambda x: x['name'])
                documents_by_type[category] = files
                total_count += len(files)
        
        return {
            "documents_by_type": documents_by_type,
            "total_count": total_count
        }
    
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

@api_router.post("/documents/reindex")
async def reindex_documents(background_tasks: BackgroundTasks, clear_cache: bool = False):
    """Trigger document reindexing
    
    Args:
        clear_cache: If True, clears cache and reprocesses all documents (full reindex)
                    If False, only processes new/modified documents (incremental)
    """
    if clear_cache:
        logger.info("Full reindex requested - will clear cache and reprocess all documents")
        background_tasks.add_task(process_documents, clear_existing=True, use_cache=False)
        return {"message": "Full document reindexing started (processing all documents)"}
    else:
        logger.info("Incremental reindex requested - will process only new/modified documents")
        background_tasks.add_task(process_documents, clear_existing=False, use_cache=True)
        return {"message": "Incremental document reindexing started (processing changed documents only)"}

@api_router.get("/documents/cache-stats")
async def get_cache_stats():
    """Get document cache statistics"""
    try:
        stats = await document_cache.get_cache_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    allow_origin_regex=".*",
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File watcher setup
observer = None
file_handler = None
startup_time = None

@app.on_event("startup")
async def startup_event():
    """Initialize services and start file watcher"""
    global observer, file_handler, startup_time
    
    import time
    startup_time = time.time()
    
    logger.info("Starting NeuralStark API with optimized processing")
    
    # Process existing documents with caching (incremental)
    await process_documents(clear_existing=False, use_cache=True)
    
    # Start file watcher
    files_dir = Path(config_paths.FILES_DIR_STR)
    if files_dir.exists():
        file_handler = DocumentFileHandler()
        observer = Observer()
        observer.schedule(file_handler, str(files_dir), recursive=True)
        observer.start()
        logger.info(f"File watcher started for {files_dir}")
        
        # Start background task to check for pending reindexing
        asyncio.create_task(check_reindex_pending())

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global observer
    
    if observer:
        observer.stop()
        observer.join()
    
    client.close()
    logger.info("NeuralStark API shutdown complete")