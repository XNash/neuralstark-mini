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
from vector_store import VectorStoreService
from rag_service import RAGService

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

# Initialize services
doc_processor = DocumentProcessor()
vector_service = VectorStoreService()
rag_service = RAGService(vector_service, db)

# Define Models
class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    gemini_api_key: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SettingsUpdate(BaseModel):
    gemini_api_key: str

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
        self.pending_reindex = False
        
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

# Background task to process documents
async def process_documents(clear_existing: bool = False):
    """Process all documents in files directory and update vector store
    
    Args:
        clear_existing: If True, clears existing vector store before reindexing
    """
    try:
        # Use relative path from backend directory
        files_dir = Path(__file__).parent.parent / "files"
        if not files_dir.exists():
            logger.warning("Files directory does not exist, creating it...")
            files_dir.mkdir(parents=True, exist_ok=True)
            return
        
        supported_extensions = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.odt', '.txt', '.md', '.json', '.csv']
        files = [f for f in files_dir.rglob('*') if f.suffix.lower() in supported_extensions]
        
        logger.info(f"Found {len(files)} documents to process (clear_existing={clear_existing})")
        
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
        
        # Clear vector store if requested (for full reindex)
        if clear_existing:
            logger.info("Clearing existing vector store for full reindex...")
            vector_service.clear_collection()
        
        total_chunks = 0
        successful_files = 0
        failed_files = []
        
        for file_path in files:
            try:
                logger.info(f"Processing document: {file_path.name}")
                
                # Extract text from document
                text_chunks = doc_processor.process_document(str(file_path))
                
                if text_chunks:
                    # Add to vector store with enhanced metadata
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
                    
                    vector_service.add_documents(
                        texts=text_chunks,
                        metadata=file_metadata
                    )
                    
                    total_chunks += len(text_chunks)
                    successful_files += 1
                    logger.info(f"✓ Processed {file_path.name}: {len(text_chunks)} chunks")
                else:
                    logger.warning(f"✗ No text extracted from {file_path.name}")
                    failed_files.append(file_path.name)
            except Exception as e:
                logger.error(f"✗ Error processing {file_path.name}: {e}", exc_info=True)
                failed_files.append(file_path.name)
        
        # Save updated timestamp to database
        await db.document_status.update_one(
            {"id": "status"},
            {
                "$set": {
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "total_documents": len(files),
                    "successful_files": successful_files,
                    "failed_files": failed_files,
                    "total_chunks": total_chunks
                }
            },
            upsert=True
        )
        
        logger.info(f"Document processing completed: {successful_files}/{len(files)} files successful, {total_chunks} total chunks")
        if failed_files:
            logger.warning(f"Failed to process: {', '.join(failed_files)}")
    except Exception as e:
        logger.error(f"Error in process_documents: {e}", exc_info=True)

# API Routes
@api_router.get("/")
async def root():
    return {"message": "RAG Platform API", "status": "running"}

@api_router.get("/settings", response_model=Settings)
async def get_settings():
    """Get current settings"""
    settings = await db.settings.find_one({"id": "main"}, {"_id": 0})
    if not settings:
        # Return default settings
        return Settings(id="main", gemini_api_key=None)
    
    if isinstance(settings.get('updated_at'), str):
        settings['updated_at'] = datetime.fromisoformat(settings['updated_at'])
    
    return Settings(**settings)

@api_router.post("/settings", response_model=Settings)
async def update_settings(settings_update: SettingsUpdate):
    """Update settings (API key)"""
    settings_obj = Settings(
        id="main",
        gemini_api_key=settings_update.gemini_api_key
    )
    
    doc = settings_obj.model_dump()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.settings.update_one(
        {"id": "main"},
        {"$set": doc},
        upsert=True
    )
    
    # Update RAG service with new API key
    rag_service.update_api_key(settings_update.gemini_api_key)
    
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
    
    files_dir = Path(__file__).parent.parent / "files"
    supported_extensions = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.odt', '.txt', '.md', '.json', '.csv']
    files = [f for f in files_dir.rglob('*') if f.suffix.lower() in supported_extensions] if files_dir.exists() else []
    
    return DocumentStatus(
        total_documents=len(files),
        indexed_documents=vector_service.get_collection_count(),
        last_updated=status.get('last_updated') if status else None
    )

@api_router.post("/documents/reindex")
async def reindex_documents(background_tasks: BackgroundTasks):
    """Trigger full document reindexing (clears existing index and rebuilds)"""
    logger.info("Reindex requested - will clear existing index and rebuild")
    background_tasks.add_task(process_documents, clear_existing=True)
    return {"message": "Document reindexing started (clearing existing index and rebuilding)"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.on_event("startup")
async def startup_event():
    """Initialize services and start file watcher"""
    global observer, file_handler
    
    logger.info("Starting RAG Platform API")
    
    # Process existing documents
    await process_documents()
    
    # Start file watcher
    files_dir = Path(__file__).parent.parent / "files"
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
    logger.info("RAG Platform API shutdown complete")