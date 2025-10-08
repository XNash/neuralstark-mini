#!/bin/bash

###############################################################################
# RAG Platform - One-Click Setup and Run Script
# This script installs all dependencies and starts the platform
###############################################################################

set -e  # Exit on any error

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${GREEN}[RAG Platform]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_step() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

# Check if script is run from correct directory
if [ ! -f "run.sh" ]; then
    print_error "Please run this script from the /app directory"
    exit 1
fi

print_step "🚀 RAG Platform Setup & Launch"

# Step 1: Check and install system dependencies
print_step "📦 Step 1/6: Installing System Dependencies"

print_message "Checking for tesseract-ocr..."
if ! command -v tesseract &> /dev/null; then
    print_message "Installing tesseract-ocr and language packs..."
    apt-get update > /dev/null 2>&1
    apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-fra poppler-utils > /dev/null 2>&1
    print_message "✅ Tesseract OCR installed successfully"
else
    print_message "✅ Tesseract OCR already installed"
fi

print_message "Checking for poppler-utils..."
if ! command -v pdftotext &> /dev/null; then
    print_message "Installing poppler-utils..."
    apt-get install -y poppler-utils > /dev/null 2>&1
    print_message "✅ Poppler-utils installed successfully"
else
    print_message "✅ Poppler-utils already installed"
fi

# Step 2: Create necessary directories and set permissions
print_step "📁 Step 2/6: Setting Up Directories & Permissions"

print_message "Creating files directory..."
mkdir -p files
print_message "✅ Files directory ready"

print_message "Creating ChromaDB directory..."
mkdir -p backend/chroma_db
print_message "✅ ChromaDB directory ready"

print_message "Setting permissions for all project files..."
chmod -R 777 backend
chmod -R 777 frontend
chmod -R 777 files
chmod 777 run.sh
chmod 777 README.md 2>/dev/null || true
chmod 777 QUICKSTART.md 2>/dev/null || true
print_message "✅ Permissions set to 777 for all project files"

# Step 3: Install backend dependencies
print_step "🐍 Step 3/6: Installing Python Backend Dependencies"

cd "$SCRIPT_DIR/backend"

print_message "Installing emergentintegrations library..."
pip install -q emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

print_message "Installing RAG and document processing libraries..."
pip install -q chromadb sentence-transformers langchain langchain-community watchdog

print_message "Installing document processors..."
pip install -q pypdf pdfplumber python-docx openpyxl odfpy pytesseract pillow pdf2image

print_message "Updating requirements.txt..."
pip freeze > requirements.txt

print_message "✅ All Python dependencies installed"

cd "$SCRIPT_DIR"

# Step 4: Install frontend dependencies
print_step "⚛️  Step 4/6: Installing Frontend Dependencies"

cd "$SCRIPT_DIR/frontend"

if [ ! -d "node_modules" ]; then
    print_message "Installing frontend packages with yarn..."
    yarn install --silent > /dev/null 2>&1
    print_message "✅ Frontend dependencies installed"
else
    print_message "✅ Frontend dependencies already installed"
fi

cd "$SCRIPT_DIR"

# Step 5: Verify environment configuration
print_step "⚙️  Step 5/6: Verifying Configuration"

cd "$SCRIPT_DIR"

print_message "Checking backend .env file..."
if [ -f "backend/.env" ]; then
    print_message "✅ Backend .env exists"
else
    print_warning "Backend .env not found, this may cause issues"
fi

print_message "Checking frontend .env file..."
if [ -f "frontend/.env" ]; then
    print_message "✅ Frontend .env exists"
else
    print_warning "Frontend .env not found, this may cause issues"
fi

# Check if sample documents exist
print_message "Checking sample documents..."
DOC_COUNT=$(find files -type f 2>/dev/null | wc -l)
if [ "$DOC_COUNT" -gt 0 ]; then
    print_message "✅ Found $DOC_COUNT document(s) in files directory"
else
    print_warning "No documents found in files directory - Add documents to get started"
fi

# Step 6: Start services
print_step "🚀 Step 6/6: Starting Services"

print_message "Starting all services with supervisor..."
sudo supervisorctl restart all > /dev/null 2>&1

sleep 3

print_message "Checking service status..."
sudo supervisorctl status

# Wait for services to be fully ready
print_message "Waiting for services to initialize..."
sleep 8

# Check backend health
print_message "Checking backend health..."
BACKEND_STATUS=$(curl -s http://localhost:8001/api/ 2>/dev/null || echo "failed")
if [[ $BACKEND_STATUS == *"RAG Platform API"* ]]; then
    print_message "✅ Backend is running"
else
    print_error "Backend may not be running properly. Check logs with: tail -f /var/log/supervisor/backend.err.log"
fi

# Check frontend
print_message "Checking frontend..."
sleep 2
FRONTEND_STATUS=$(curl -s http://localhost:3000 2>/dev/null | head -c 100 || echo "failed")
if [[ $FRONTEND_STATUS == *"<!DOCTYPE html>"* ]] || [[ $FRONTEND_STATUS != "failed" ]]; then
    print_message "✅ Frontend is running"
else
    print_error "Frontend may not be running properly. Check logs with: tail -f /var/log/supervisor/frontend.out.log"
fi

# Final summary
print_step "✅ RAG Platform Setup Complete!"

echo -e "${GREEN}"
cat << "EOF"
   ____  ___   ______   ____  __      __  ____                 
  / __ \/   | / ____/  / __ \/ /___ _/ /_/ __/___  _________ ___
 / /_/ / /| |/ / __   / /_/ / / __ `/ __/ /_/ __ \/ ___/ __ `__ \
/ _, _/ ___ / /_/ /  / ____/ / /_/ / /_/ __/ /_/ / /  / / / / / /
/_/ |_/_/  |_\____/  /_/   /_/\__,_/\__/_/  \____/_/  /_/ /_/ /_/ 
                                                                   
EOF
echo -e "${NC}"

echo ""
print_message "🎉 Platform is ready to use!"
echo ""
echo -e "${BLUE}📍 Access Points:${NC}"
echo -e "   Frontend: ${GREEN}Check your deployment URL${NC}"
echo -e "   Backend API: ${GREEN}http://localhost:8001/api/${NC}"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo -e "   1. Open the frontend in your browser"
echo -e "   2. Go to ${YELLOW}Settings${NC} page"
echo -e "   3. Add your ${YELLOW}Gemini API key${NC} (get it from https://aistudio.google.com/app/apikey)"
echo -e "   4. Add documents to ${YELLOW}/app/files${NC} directory"
echo -e "   5. Start chatting with your documents! 💬"
echo ""
echo -e "${BLUE}🔧 Useful Commands:${NC}"
echo -e "   View backend logs:  ${YELLOW}tail -f /var/log/supervisor/backend.err.log${NC}"
echo -e "   View frontend logs: ${YELLOW}tail -f /var/log/supervisor/frontend.out.log${NC}"
echo -e "   Restart services:   ${YELLOW}sudo supervisorctl restart all${NC}"
echo -e "   Check status:       ${YELLOW}sudo supervisorctl status${NC}"
echo ""
echo -e "${BLUE}📚 Sample Documents:${NC}"
echo -e "   • company_info.md - Company information (English + French)"
echo -e "   • products.txt    - Product catalog"
echo -e "   • faq.json        - Frequently asked questions"
echo ""
echo -e "${GREEN}Happy chatting with your documents! 🚀${NC}"
echo ""

# Return to original directory
cd /app

exit 0
