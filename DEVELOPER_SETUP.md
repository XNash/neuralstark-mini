# 🛠️ NeuralStark - Developer Setup Guide

This guide will help developers set up and run NeuralStark on their local machines for development purposes.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Windows Setup](#windows-setup)
- [Linux Setup](#linux-setup)
- [macOS Setup](#macos-setup)
- [Manual Setup (All Platforms)](#manual-setup-all-platforms)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)
- [API Documentation](#api-documentation)

---

## 🔧 Prerequisites

### Common Requirements (All Platforms)

- **Python**: 3.9 or higher
- **Node.js**: 18.x or higher
- **MongoDB**: 4.4 or higher (running locally or accessible via network)
- **Yarn**: Package manager for frontend
- **Git**: Version control

### Platform-Specific Requirements

#### Windows
- **PowerShell**: 5.1 or higher (included with Windows 10/11)
- **Visual C++ Build Tools**: For some Python packages
  - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

#### Linux
- **Build essentials**: gcc, g++, make
- **Python development headers**: python3-dev
- **MongoDB**: Can be installed locally or use Docker

---

## 🪟 Windows Setup

### Option 1: Automated Setup (Recommended)

1. **Clone the repository**
   ```powershell
   git clone <your-repository-url>
   cd neuralstark
   ```

2. **Run the automated setup script**
   ```powershell
   .\setup.ps1
   ```

   This script will:
   - Install Python and Node.js dependencies
   - Set up environment variables
   - Create necessary directories
   - Initialize the database

3. **Start the application**
   ```powershell
   .\start.ps1
   ```

### Option 2: Manual Setup (Windows)

1. **Clone the repository**
   ```powershell
   git clone <your-repository-url>
   cd neuralstark
   ```

2. **Set up Python virtual environment**
   ```powershell
   # Navigate to backend directory
   cd backend
   
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   .\venv\Scripts\Activate.ps1
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Set up backend environment variables**
   ```powershell
   # Create .env file in backend directory
   @"
   MONGO_URL=mongodb://localhost:27017/neuralstark
   FILES_DIR=../files
   VECTOR_DB_PATH=./chroma_db
   "@ | Out-File -FilePath .env -Encoding utf8
   ```

4. **Set up frontend**
   ```powershell
   # Navigate to frontend directory (from root)
   cd ..\frontend
   
   # Install dependencies
   yarn install
   ```

5. **Set up frontend environment variables**
   ```powershell
   # Create .env file in frontend directory
   @"
   REACT_APP_BACKEND_URL=http://localhost:8001
   "@ | Out-File -FilePath .env -Encoding utf8
   ```

6. **Start MongoDB**
   ```powershell
   # If MongoDB is installed as a service, ensure it's running
   net start MongoDB
   
   # Or start MongoDB manually
   mongod --dbpath C:\data\db
   ```

7. **Start the backend server**
   ```powershell
   # In backend directory with venv activated
   cd ..\backend
   .\venv\Scripts\Activate.ps1
   uvicorn server:app --host 0.0.0.0 --port 8001 --reload
   ```

8. **Start the frontend (in a new terminal)**
   ```powershell
   cd frontend
   yarn start
   ```

9. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001
   - API Docs: http://localhost:8001/docs

---

## 🐧 Linux Setup

### Option 1: Automated Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd neuralstark
   ```

2. **Run the automated setup script**
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

   This script will:
   - Check and install required dependencies
   - Set up Python virtual environment
   - Install all Python and Node.js packages
   - Configure environment variables
   - Start all services

### Option 2: Manual Setup (Linux)

1. **Install system dependencies**
   
   **Ubuntu/Debian:**
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip python3-venv python3-dev \
                      nodejs npm mongodb build-essential git curl
   
   # Install Yarn
   npm install -g yarn
   ```

   **Fedora/RHEL/CentOS:**
   ```bash
   sudo dnf install -y python3 python3-pip python3-devel \
                      nodejs npm mongodb-server gcc gcc-c++ make git curl
   
   # Install Yarn
   npm install -g yarn
   ```

   **Arch Linux:**
   ```bash
   sudo pacman -S python python-pip nodejs npm mongodb gcc make git curl yarn
   ```

2. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd neuralstark
   ```

3. **Set up Python virtual environment**
   ```bash
   # Navigate to backend directory
   cd backend
   
   # Create virtual environment
   python3 -m venv venv
   
   # Activate virtual environment
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

4. **Set up backend environment variables**
   ```bash
   # Create .env file in backend directory
   cat > .env << EOF
   MONGO_URL=mongodb://localhost:27017/neuralstark
   FILES_DIR=../files
   VECTOR_DB_PATH=./chroma_db
   EOF
   ```

5. **Set up frontend**
   ```bash
   # Navigate to frontend directory (from root)
   cd ../frontend
   
   # Install dependencies
   yarn install
   ```

6. **Set up frontend environment variables**
   ```bash
   # Create .env file in frontend directory
   cat > .env << EOF
   REACT_APP_BACKEND_URL=http://localhost:8001
   EOF
   ```

7. **Start MongoDB**
   ```bash
   # Start MongoDB service
   sudo systemctl start mongodb
   
   # Enable MongoDB to start on boot
   sudo systemctl enable mongodb
   
   # Check MongoDB status
   sudo systemctl status mongodb
   ```

8. **Start the backend server**
   ```bash
   # In backend directory with venv activated
   cd ../backend
   source venv/bin/activate
   uvicorn server:app --host 0.0.0.0 --port 8001 --reload
   ```

9. **Start the frontend (in a new terminal)**
   ```bash
   cd frontend
   yarn start
   ```

10. **Access the application**
    - Frontend: http://localhost:3000
    - Backend API: http://localhost:8001
    - API Docs: http://localhost:8001/docs

---

## 🍎 macOS Setup

### Prerequisites Installation

1. **Install Homebrew** (if not installed)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install required packages**
   ```bash
   brew install python@3.11 node mongodb-community yarn git
   ```

3. **Start MongoDB**
   ```bash
   brew services start mongodb-community
   ```

4. **Follow the Linux manual setup steps** (steps 2-10 from Linux setup)

---

## 🔨 Manual Setup (All Platforms)

### Backend Setup Details

The backend is built with FastAPI and requires the following components:

**Key Dependencies:**
- FastAPI - Web framework
- uvicorn - ASGI server
- motor - Async MongoDB driver
- chromadb - Vector database
- sentence-transformers - Embedding models
- emergentintegrations - Gemini API integration
- python-docx, openpyxl, PyPDF2 - Document processors

**Environment Variables (backend/.env):**
```env
# MongoDB connection string
MONGO_URL=mongodb://localhost:27017/neuralstark

# Documents directory (relative to backend/)
FILES_DIR=../files

# Vector database storage path
VECTOR_DB_PATH=./chroma_db

# Optional: Gemini API key (can also be configured via UI)
GEMINI_API_KEY=your_api_key_here
```

**Running the backend:**
```bash
cd backend
source venv/bin/activate  # On Linux/macOS
# or
.\venv\Scripts\Activate.ps1  # On Windows

uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup Details

The frontend is a React application with Tailwind CSS.

**Key Dependencies:**
- React 19
- React Router DOM
- Axios for API calls
- Tailwind CSS for styling
- Radix UI components

**Environment Variables (frontend/.env):**
```env
# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8001
```

**Running the frontend:**
```bash
cd frontend
yarn start
```

The development server will start at http://localhost:3000 with hot reload enabled.

---

## 📁 Project Structure

```
neuralstark/
├── backend/                    # FastAPI backend
│   ├── server.py              # Main API server
│   ├── rag_service.py         # RAG logic and Gemini integration
│   ├── vector_store.py        # ChromaDB vector store
│   ├── vector_store_optimized.py  # Optimized vector operations
│   ├── document_processor.py  # Document parsing and chunking
│   ├── document_processor_optimized.py  # Optimized processing
│   ├── document_cache.py      # Caching layer
│   ├── config_paths.py        # Path configurations
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment variables
│   └── chroma_db/            # Vector database storage (auto-created)
│
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── App.js            # Main application component
│   │   ├── App.css           # Application styles
│   │   └── App-material.css  # Material design styles
│   ├── public/               # Static assets
│   ├── package.json          # Node.js dependencies
│   ├── .env                  # Environment variables
│   └── tailwind.config.js    # Tailwind CSS configuration
│
├── files/                    # Document storage directory
│   ├── company_info.md       # Sample documents
│   ├── faq.json
│   └── products.txt
│
├── tests/                    # Test files
│   └── __init__.py
│
├── scripts/                  # Utility scripts
│
├── run.sh                    # Linux/macOS startup script
├── setup.ps1                 # Windows setup script
├── start.ps1                 # Windows startup script
├── stop.ps1                  # Windows stop script
├── README.md                 # Project documentation
├── DEVELOPER_SETUP.md        # This file
└── test_result.md           # Test results and history
```

---

## 🔄 Development Workflow

### 1. Creating New Features

**Backend (Python/FastAPI):**
1. Create new routes in `backend/server.py` or separate router files
2. Update database models in appropriate service files
3. Test endpoints using FastAPI's automatic documentation at `/docs`

**Frontend (React):**
1. Create new components in `frontend/src/`
2. Update `App.js` for routing and state management
3. Style with Tailwind CSS classes

### 2. Adding New Document Types

1. **Update Document Processor** (`backend/document_processor.py`):
   ```python
   def process_file(self, filepath):
       # Add new file extension handling
       if filepath.endswith('.newtype'):
           return self.extract_from_newtype(filepath)
   ```

2. **Add Extraction Logic**:
   ```python
   def extract_from_newtype(self, filepath):
       # Implement extraction logic
       text = extract_text_from_newtype(filepath)
       return self.chunk_text(text)
   ```

3. **Update UI** - Add new format to Documents page in `App.js`

### 3. Testing Changes

**Backend Testing:**
```bash
# Run backend tests
cd backend
source venv/bin/activate
python -m pytest tests/

# Or test specific endpoints with curl
curl http://localhost:8001/api/health
```

**Frontend Testing:**
```bash
cd frontend
yarn test
```

**Manual Testing:**
- Use the application at http://localhost:3000
- Check browser console for JavaScript errors
- Monitor backend logs in the terminal

### 4. Database Operations

**Connecting to MongoDB:**
```bash
# Using MongoDB shell
mongo mongodb://localhost:27017/neuralstark

# Or using MongoDB Compass (GUI)
# Connection string: mongodb://localhost:27017/neuralstark
```

**Common Database Operations:**
```javascript
// Show all collections
show collections

// Query settings
db.settings.find()

// Query chat history
db.chat_messages.find()

// Clear chat history
db.chat_messages.deleteMany({})

// Clear cache
db.document_cache.deleteMany({})
```

### 5. Code Style and Linting

**Python (Backend):**
```bash
# Install development tools
pip install black flake8 pylint

# Format code
black backend/

# Check code style
flake8 backend/

# Lint code
pylint backend/*.py
```

**JavaScript (Frontend):**
```bash
# Lint and fix
yarn lint --fix

# Format with Prettier (if configured)
yarn format
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error:** `Address already in use: port 8001` or `port 3000`

**Solution:**

**Linux/macOS:**
```bash
# Find process using port 8001
lsof -i :8001
# Kill the process
kill -9 <PID>

# Find process using port 3000
lsof -i :3000
kill -9 <PID>
```

**Windows:**
```powershell
# Find process using port 8001
netstat -ano | findstr :8001
# Kill the process
taskkill /PID <PID> /F

# Find process using port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

#### 2. MongoDB Connection Failed

**Error:** `ServerSelectionTimeoutError` or `Connection refused`

**Solutions:**
- Ensure MongoDB is running: `sudo systemctl status mongodb` (Linux) or check Services (Windows)
- Check MongoDB connection string in `backend/.env`
- Verify MongoDB port (default: 27017) is not blocked by firewall
- Test connection: `mongo mongodb://localhost:27017`

#### 3. Python Package Installation Fails

**Error:** Build errors or compilation failures

**Solutions:**

**Windows:**
- Install Visual C++ Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Update pip: `python -m pip install --upgrade pip`

**Linux:**
- Install build essentials: `sudo apt install build-essential python3-dev`
- Update pip: `pip install --upgrade pip`

#### 4. Frontend Not Loading

**Error:** Blank page or connection refused

**Solutions:**
- Check if backend is running at http://localhost:8001/api/health
- Verify `REACT_APP_BACKEND_URL` in `frontend/.env`
- Clear browser cache and hard refresh (Ctrl+Shift+R)
- Check browser console for errors (F12)
- Restart frontend: `yarn start`

#### 5. Document Processing Errors

**Error:** Documents not being indexed or processed

**Solutions:**
- Check `files/` directory exists and contains documents
- Verify file permissions (read access required)
- Check backend logs for specific errors
- Manually trigger reindex via Documents page
- Ensure document formats are supported

#### 6. API Key Issues

**Error:** Gemini API errors or quota exceeded

**Solutions:**
- Verify API key in Settings page
- Check API key has sufficient quota
- Visit https://aistudio.google.com/app/apikey to manage keys
- Ensure API key has correct permissions
- Check for rate limiting errors in backend logs

#### 7. Virtual Environment Issues

**Error:** Module not found or wrong Python version

**Solutions:**

**Linux/macOS:**
```bash
# Recreate virtual environment
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```powershell
# Recreate virtual environment
cd backend
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 📚 API Documentation

### Backend API Endpoints

Once the backend is running, visit http://localhost:8001/docs for interactive API documentation.

#### Key Endpoints

**Health Check:**
```http
GET /api/health
Response: {
  "status": "healthy",
  "mongodb": "connected",
  "documents": { "total": 3, "indexed_chunks": 6 }
}
```

**Settings:**
```http
GET /api/settings
Response: { "id": "...", "gemini_api_key": "..." }

POST /api/settings
Body: { "gemini_api_key": "your-key" }
Response: { "success": true, "message": "Settings saved successfully" }
```

**Document Status:**
```http
GET /api/documents/status
Response: {
  "total_documents": 3,
  "indexed_documents": 6,
  "last_updated": "2025-01-10T..."
}
```

**Chat:**
```http
POST /api/chat
Body: {
  "message": "What are your products?",
  "session_id": "session_123"
}
Response: {
  "response": "Based on the documents...",
  "session_id": "session_123",
  "sources": ["products.txt", "company_info.md"]
}
```

**Reindex Documents:**
```http
POST /api/documents/reindex
Body: { "clear_cache": false }
Response: { "success": true, "message": "Reindexing started" }
```

---

## 🚀 Production Deployment

For production deployment instructions, see:
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Complete deployment guide
- [DOCKER.md](./DOCKER.md) - Docker deployment
- [QUICKSTART.md](./QUICKSTART.md) - Quick deployment reference

---

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Make your changes and commit:** `git commit -m 'Add amazing feature'`
4. **Push to the branch:** `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Code Guidelines

- Follow PEP 8 for Python code
- Use ESLint rules for JavaScript/React
- Write meaningful commit messages
- Add comments for complex logic
- Update documentation for new features
- Write tests for new functionality

---

## 📖 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

---

## 📝 License

See the [LICENSE](./LICENSE) file for details.

---

## 💬 Support

- **Issues:** Report bugs or request features on GitHub Issues
- **Documentation:** Check README.md and other .md files
- **Community:** Join our Discord/Slack (if applicable)

---

**Happy Coding! 🚀**

Built with ❤️ by the NeuralStark Team
