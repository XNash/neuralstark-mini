# 🤖 RAG Platform - AI-Powered Document Q&A System

A full-stack Retrieval-Augmented Generation (RAG) platform that allows users to chat with their documents using AI. The system automatically indexes documents and uses them as context for answering questions.

## 🌟 Features

### Core Functionality
- **🔍 Automatic Document Indexing**: Watches `/app/files` directory for new or modified documents
- **💬 AI-Powered Chat**: Chat with your documents using Gemini 2.5 Flash
- **🌐 Multilingual Support**: Optimized for English and French with BAAI embeddings
- **📊 Real-time Status**: Monitor indexed documents and processing status
- **🔄 Manual Reindexing**: Trigger document reindexing on demand
- **📝 Chat History**: Maintains conversation history per session

### Supported Document Formats
- **📄 PDF** - With OCR support for scanned documents
- **📝 Word Documents** - `.doc` (legacy) and `.docx` (modern) with image OCR
- **📊 Excel Spreadsheets** - `.xls` (legacy) and `.xlsx` (modern)
- **📃 OpenDocument** - `.odt` files
- **📋 Text Files** - `.txt` and `.md` (Markdown)
- **💾 Data Files** - `.json` and `.csv`

## 🏗️ Architecture

### Technology Stack

**Backend (FastAPI + Python)**
- FastAPI for REST API
- ChromaDB for vector storage
- Sentence-Transformers with BAAI/bge-base-en-v1.5 for embeddings
- Motor (AsyncIO MongoDB driver)
- Watchdog for file system monitoring
- Various document processors (PyPDF, python-docx, openpyxl, etc.)
- Tesseract OCR for scanned documents

**Frontend (React)**
- React 18 with Hooks
- Tailwind CSS for styling
- Responsive design
- Real-time chat interface

**Database**
- MongoDB for storing settings, chat history, and metadata

**AI Integration**
- Google Gemini 2.5 Flash via emergentintegrations library
- RAG (Retrieval-Augmented Generation) architecture

## 🚀 Getting Started

### Configuration

**Backend `.env` file** (`/app/backend/.env`):
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"
```

**Gemini API Key:**
1. Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Add it via the Settings page in the web UI

### Using the Platform

1. **Access the application** at your deployment URL
2. **Configure API Key**: Go to Settings page and add your Gemini API key
3. **Add Documents**: Place files in `/app/files` directory
4. **Wait for Indexing**: Documents are automatically indexed (5-second check interval)
5. **Start Chatting**: Ask questions about your documents in the Chat page

## 📚 API Documentation

### Settings Endpoints

**Get Settings**
```http
GET /api/settings
```

**Update Settings**
```http
POST /api/settings
Content-Type: application/json

{
  "gemini_api_key": "your-gemini-api-key"
}
```

### Document Endpoints

**Get Document Status**
```http
GET /api/documents/status
```

**Trigger Reindexing**
```http
POST /api/documents/reindex
```

### Chat Endpoints

**Send Chat Message**
```http
POST /api/chat
Content-Type: application/json

{
  "message": "What products does TechCorp offer?",
  "session_id": "optional-session-id"
}
```

**Get Chat History**
```http
GET /api/chat/history/{session_id}
```

## 🗂️ Project Structure

```
/app/
├── backend/                    # FastAPI backend
│   ├── server.py              # Main FastAPI application
│   ├── document_processor.py  # Document parsing and chunking
│   ├── vector_store.py        # ChromaDB vector store service
│   ├── rag_service.py         # RAG logic and Gemini integration
│   ├── requirements.txt       # Python dependencies
│   ├── chroma_db/            # ChromaDB persistent storage
│   └── .env                  # Environment variables
│
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── App.js            # Main React component
│   │   ├── App.css           # Styling
│   │   └── index.js          # Entry point
│   └── .env                  # Frontend environment variables
│
├── files/                     # Document storage (watched directory)
│   ├── company_info.md       # Example: Company information
│   ├── products.txt          # Example: Product catalog
│   └── faq.json             # Example: FAQ data
│
└── README.md                 # This file
```

## 🎯 How It Works

### RAG Pipeline

1. **Document Processing**: Files detected in `/app/files` → Text extraction with OCR → Chunking with overlap
2. **Embedding & Indexing**: Chunks converted to embeddings → Stored in ChromaDB with metadata
3. **Query Processing**: User question embedded → Top K relevant chunks retrieved from vector store
4. **Response Generation**: Context + query sent to Gemini → Response based on documents → Sources returned

### Key Features

- **Simple Architecture**: Prioritized simplicity and coherence
- **Persistent Storage**: ChromaDB with disk persistence
- **Multilingual**: BAAI embeddings work well for English and French
- **Async Processing**: Non-blocking document processing
- **Session-based Chat**: Each conversation has unique session
- **Source Attribution**: Responses include source documents with relevance scores

## 🔍 Troubleshooting

### Documents Not Indexing
1. Check if files are in `/app/files`
2. Verify file format is supported
3. Trigger manual reindexing via Settings page

### Chat Not Working
1. Verify Gemini API key is set in Settings
2. Check if documents are indexed (status should show >0)
3. Check backend logs for errors

## 📊 Example Documents

The platform includes three sample documents:
- `company_info.md` - Company information in English and French
- `products.txt` - Product catalog with pricing
- `faq.json` - Frequently asked questions

Try asking:
- "What products does TechCorp offer?"
- "What are the office hours?"
- "Quelles sont les valeurs de TechCorp?" (French)
- "What is the refund policy?"

## 🎉 Acknowledgments

- **ChromaDB** - Vector database
- **Sentence-Transformers** - Embedding models
- **Google Gemini** - Language model
- **FastAPI** - Backend framework
- **React** - Frontend framework

---

**Built with ❤️ for intelligent document interaction**
