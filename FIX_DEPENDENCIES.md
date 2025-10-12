# Quick Fix for Missing Dependencies

Your setup is almost complete! Just need to install the missing Python packages.

## Run these commands on your machine:

```bash
cd ~/Documents/projects/neuralstark-mini

# Activate virtual environment
source .venv/bin/activate

# Install all missing dependencies
pip install watchdog chromadb sentence-transformers langchain langchain-community pypdf pdfplumber python-docx openpyxl odfpy pytesseract pillow pdf2image google-generativeai python-multipart

# Update requirements.txt
pip freeze > backend/requirements.txt

# Restart backend
sudo supervisorctl restart backend

# Check if it's running
curl http://localhost:8001/api/
```

## What's happening:

The script installed FastAPI and other critical packages, but missed:
- **watchdog** - For file monitoring
- **chromadb** - Vector database
- **sentence-transformers** - For embeddings
- **langchain** - RAG framework
- **google-generativeai** - Gemini API client (replacing emergentintegrations which doesn't support Python 3.13)
- Document processing libraries (pypdf, pdfplumber, python-docx, etc.)

## After installation:

1. Backend should start successfully
2. You can add your Gemini API key via the Settings page at http://localhost:3000
3. Start chatting with your documents!

## If you still see errors:

```bash
# Check backend logs
tail -20 /var/log/supervisor/backend.err.log

# Try restarting
sudo supervisorctl restart all
```
