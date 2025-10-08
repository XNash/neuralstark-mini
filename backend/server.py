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

# Background task to process documents
async def process_documents():
    """Process all documents in /app/files and update vector store"""
    try:
        files_dir = Path("/app/files")
        if not files_dir.exists():
            logger.warning("Files directory does not exist")
            return
        
        supported_extensions = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.odt', '.txt', '.md', '.json', '.csv']
        files = [f for f in files_dir.rglob('*') if f.suffix.lower() in supported_extensions]
        
        logger.info(f"Found {len(files)} documents to process")
        
        for file_path in files:
            try:
                # Extract text from document
                text_chunks = doc_processor.process_document(str(file_path))
                
                if text_chunks:
                    # Add to vector store
                    vector_service.add_documents(
                        texts=text_chunks,
                        metadata=[{"source": file_path.name, "chunk_index": i} for i in range(len(text_chunks))]
                    )
                    logger.info(f"Processed {file_path.name}: {len(text_chunks)} chunks")
                else:
                    logger.warning(f"No text extracted from {file_path.name}")
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
        
        # Save updated timestamp to database
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
        
        logger.info("Document processing completed")
    except Exception as e:
        logger.error(f"Error in process_documents: {e}")

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
    """Chat with RAG agent"""
    try:
        # Get API key from settings
        settings = await db.settings.find_one({"id": "main"})
        if not settings or not settings.get('gemini_api_key'):
            raise HTTPException(status_code=400, detail="Gemini API key not configured. Please add it in Settings.")
        
        # Generate session_id if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get chat history for this session
        chat_history = await db.chat_messages.find(
            {"session_id": session_id},
            {"_id": 0}
        ).sort("timestamp", 1).to_list(50)
        
        # Save user message
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.message
        )
        user_doc = user_message.model_dump()
        user_doc['timestamp'] = user_doc['timestamp'].isoformat()
        await db.chat_messages.insert_one(user_doc)
        
        # Get response from RAG service
        response_text, sources = await rag_service.get_response(
            query=request.message,
            session_id=session_id,
            api_key=settings['gemini_api_key'],
            chat_history=chat_history
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
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            sources=sources
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    
    files_dir = Path("/app/files")
    supported_extensions = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.odt', '.txt', '.md', '.json', '.csv']
    files = [f for f in files_dir.rglob('*') if f.suffix.lower() in supported_extensions] if files_dir.exists() else []
    
    return DocumentStatus(
        total_documents=len(files),
        indexed_documents=vector_service.get_collection_count(),
        last_updated=status.get('last_updated') if status else None
    )

@api_router.post("/documents/reindex")
async def reindex_documents(background_tasks: BackgroundTasks):
    """Trigger document reindexing"""
    background_tasks.add_task(process_documents)
    return {"message": "Document reindexing started"}

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
    files_dir = Path("/app/files")
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