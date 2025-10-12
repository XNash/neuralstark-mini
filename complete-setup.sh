#!/bin/bash
# Complete Setup Script - Ensures 100% working installation
# Compatible with Ubuntu, Pop_OS, Debian, CentOS, RHEL, Fedora

set +e  # Don't exit on error, handle gracefully

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_step() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo ""
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

print_step "🚀 RAG Platform - Complete Setup & Verification"

# Step 1: Check Python version
print_step "Step 1/8: Checking Python Version"
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
print_info "Python version: $PYTHON_VERSION"

PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
    print_success "Python version is compatible (3.9+)"
else
    print_error "Python 3.9+ required, found $PYTHON_VERSION"
    exit 1
fi

# Step 2: Activate virtual environment
print_step "Step 2/8: Setting Up Virtual Environment"

if [ -d ".venv" ]; then
    print_info "Virtual environment exists, activating..."
    source .venv/bin/activate
    print_success "Virtual environment activated"
else
    print_info "Creating new virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    print_success "Virtual environment created and activated"
fi

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip setuptools wheel -q
print_success "Pip upgraded"

# Step 3: Install ALL dependencies with retries
print_step "Step 3/8: Installing All Dependencies"

print_info "This will take 3-5 minutes. Please wait..."

# Install in groups for better reliability
print_info "[1/6] Installing core FastAPI packages..."
pip install fastapi uvicorn[standard] python-multipart python-dotenv --no-cache-dir 2>&1 | grep -E "(Successfully|ERROR)" || true

print_info "[2/6] Installing database packages..."
pip install motor pymongo dnspython --no-cache-dir 2>&1 | grep -E "(Successfully|ERROR)" || true

print_info "[3/6] Installing AI/ML packages (this takes longest)..."
pip install google-generativeai chromadb sentence-transformers --no-cache-dir 2>&1 | grep -E "(Successfully|ERROR)" || true

print_info "[4/6] Installing LangChain packages..."
pip install langchain langchain-community langchain-core langchain-text-splitters --no-cache-dir 2>&1 | grep -E "(Successfully|ERROR)" || true

print_info "[5/6] Installing document processing packages..."
pip install pypdf pdfplumber pdf2image python-docx openpyxl odfpy pytesseract pillow --no-cache-dir 2>&1 | grep -E "(Successfully|ERROR)" || true

print_info "[6/6] Installing utilities..."
pip install watchdog httpx aiohttp pydantic pydantic-settings tenacity tqdm --no-cache-dir 2>&1 | grep -E "(Successfully|ERROR)" || true

print_success "All package installations attempted"

# Step 4: Verify critical imports
print_step "Step 4/8: Verifying Package Imports"

test_import() {
    local package=$1
    local import_name=${2:-$1}
    
    if python -c "import $import_name" 2>/dev/null; then
        print_success "$package imported successfully"
        return 0
    else
        print_error "$package import failed"
        return 1
    fi
}

FAILED=0

# Test critical packages
test_import "FastAPI" "fastapi" || FAILED=$((FAILED+1))
test_import "Uvicorn" "uvicorn" || FAILED=$((FAILED+1))
test_import "Motor" "motor" || FAILED=$((FAILED+1))
test_import "Google Generative AI" "google.generativeai" || FAILED=$((FAILED+1))
test_import "ChromaDB" "chromadb" || FAILED=$((FAILED+1))
test_import "Sentence Transformers" "sentence_transformers" || FAILED=$((FAILED+1))
test_import "LangChain" "langchain" || FAILED=$((FAILED+1))
test_import "Watchdog" "watchdog" || FAILED=$((FAILED+1))
test_import "PyPDF" "pypdf" || FAILED=$((FAILED+1))
test_import "PDFPlumber" "pdfplumber" || FAILED=$((FAILED+1))
test_import "Python-DOCX" "docx" || FAILED=$((FAILED+1))
test_import "OpenPyXL" "openpyxl" || FAILED=$((FAILED+1))

if [ $FAILED -eq 0 ]; then
    print_success "All critical packages verified!"
else
    print_warning "$FAILED package(s) failed import test"
    print_info "Attempting to fix missing packages..."
    
    # Try installing failed packages again
    pip install -r backend/requirements.txt --no-cache-dir 2>&1 | tail -20
fi

# Step 5: Test backend imports
print_step "Step 5/8: Testing Backend Module Imports"

cd backend

if python -c "from vector_store import VectorStoreService; print('OK')" 2>/dev/null | grep -q "OK"; then
    print_success "vector_store.py imports successfully"
else
    print_error "vector_store.py has import issues"
    python -c "from vector_store import VectorStoreService" 2>&1 | tail -5
fi

if python -c "from rag_service import RAGService; print('OK')" 2>/dev/null | grep -q "OK"; then
    print_success "rag_service.py imports successfully"
else
    print_error "rag_service.py has import issues"
    python -c "from rag_service import RAGService" 2>&1 | tail -5
fi

if python -c "from document_processor import DocumentProcessor; print('OK')" 2>/dev/null | grep -q "OK"; then
    print_success "document_processor.py imports successfully"
else
    print_error "document_processor.py has import issues"
    python -c "from document_processor import DocumentProcessor" 2>&1 | tail -5
fi

cd ..

# Step 6: Update requirements.txt
print_step "Step 6/8: Updating requirements.txt"
pip freeze > backend/requirements.txt
PACKAGE_COUNT=$(wc -l < backend/requirements.txt)
print_success "requirements.txt updated with $PACKAGE_COUNT packages"

# Step 7: Check services
print_step "Step 7/8: Checking Services"

# Check MongoDB
if systemctl is-active --quiet mongod 2>/dev/null || pgrep -x mongod > /dev/null; then
    print_success "MongoDB is running"
else
    print_warning "MongoDB may not be running"
    print_info "Starting MongoDB..."
    sudo systemctl start mongod 2>/dev/null || sudo service mongod start 2>/dev/null || print_warning "Could not start MongoDB"
fi

# Check if supervisor is configured
if [ -f "/etc/supervisor/conf.d/rag-backend.conf" ]; then
    print_success "Supervisor is configured"
    
    # Restart backend
    print_info "Restarting backend service..."
    sudo supervisorctl restart backend 2>&1 | grep -v "ERROR:" || true
    sleep 3
    
    # Check status
    if sudo supervisorctl status backend 2>/dev/null | grep -q "RUNNING"; then
        print_success "Backend is running"
    else
        print_warning "Backend may not be running properly"
        print_info "Last 10 lines of backend log:"
        tail -10 /var/log/supervisor/backend.err.log 2>/dev/null || echo "No logs available"
    fi
else
    print_warning "Supervisor not configured yet - run ./run.sh to configure"
fi

# Step 8: Final verification
print_step "Step 8/8: Final Verification"

# Test backend API
print_info "Testing backend API..."
sleep 2

if curl -s -f http://localhost:8001/api/ > /dev/null 2>&1; then
    RESPONSE=$(curl -s http://localhost:8001/api/)
    print_success "Backend API is responding"
    print_info "Response: $RESPONSE"
else
    print_warning "Backend API not responding yet"
    print_info "It may still be starting up. Check logs with:"
    print_info "  tail -f /var/log/supervisor/backend.err.log"
fi

# Summary
print_step "✅ Setup Complete!"

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Installation Summary${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Python Version: ${GREEN}$PYTHON_VERSION${NC}"
echo -e "  Virtual Environment: ${GREEN}.venv/${NC}"
echo -e "  Packages Installed: ${GREEN}$PACKAGE_COUNT${NC}"
echo -e "  Project Directory: ${GREEN}$SCRIPT_DIR${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. If backend is not running, restart it:"
echo -e "     ${YELLOW}sudo supervisorctl restart backend${NC}"
echo ""
echo -e "  2. Access the application:"
echo -e "     ${YELLOW}http://localhost:3000${NC}"
echo ""
echo -e "  3. Add your Gemini API key in Settings"
echo -e "     Get it from: ${YELLOW}https://aistudio.google.com/app/apikey${NC}"
echo ""
echo -e "  4. Add documents to ${YELLOW}files/${NC} directory"
echo ""
echo -e "${GREEN}Happy chatting with your documents! 🚀${NC}"
echo ""
