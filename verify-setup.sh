#!/bin/bash

###############################################################################
# RAG Platform - Setup Verification Script
# This script verifies that all components are properly installed and running
###############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

print_check() {
    echo -e "${BLUE}[CHECK]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[✓ PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[✗ FAIL]${NC} $1"
    ERRORS=$((ERRORS + 1))
}

print_warn() {
    echo -e "${YELLOW}[⚠ WARN]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}  RAG Platform - Setup Verification${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check System Dependencies
echo -e "\n${BLUE}=== System Dependencies ===${NC}\n"

print_check "Checking Python..."
if command -v python3 &> /dev/null; then
    VERSION=$(python3 --version 2>&1)
    print_pass "Python found: $VERSION"
else
    print_fail "Python 3 not found"
fi

print_check "Checking Node.js..."
if command -v node &> /dev/null; then
    VERSION=$(node --version 2>&1)
    print_pass "Node.js found: $VERSION"
else
    print_fail "Node.js not found"
fi

print_check "Checking Yarn..."
if command -v yarn &> /dev/null; then
    VERSION=$(yarn --version 2>&1)
    print_pass "Yarn found: $VERSION"
else
    print_fail "Yarn not found"
fi

print_check "Checking MongoDB..."
if command -v mongod &> /dev/null; then
    VERSION=$(mongod --version 2>&1 | head -1)
    print_pass "MongoDB found: $VERSION"
else
    print_fail "MongoDB not found"
fi

print_check "Checking Supervisor..."
if command -v supervisorctl &> /dev/null; then
    print_pass "Supervisor found"
else
    print_warn "Supervisor not found (may not be needed in containerized environments)"
fi

print_check "Checking Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    VERSION=$(tesseract --version 2>&1 | head -1)
    print_pass "Tesseract found: $VERSION"
else
    print_warn "Tesseract OCR not found (PDF OCR will not work)"
fi

# Check Project Structure
echo -e "\n${BLUE}=== Project Structure ===${NC}\n"

print_check "Checking backend directory..."
if [ -d "/app/backend" ]; then
    print_pass "Backend directory exists"
else
    print_fail "Backend directory not found"
fi

print_check "Checking frontend directory..."
if [ -d "/app/frontend" ]; then
    print_pass "Frontend directory exists"
else
    print_fail "Frontend directory not found"
fi

print_check "Checking files directory..."
if [ -d "/app/files" ]; then
    DOC_COUNT=$(find /app/files -type f 2>/dev/null | wc -l)
    print_pass "Files directory exists ($DOC_COUNT documents)"
else
    print_warn "Files directory not found"
fi

# Check Configuration Files
echo -e "\n${BLUE}=== Configuration Files ===${NC}\n"

print_check "Checking backend .env..."
if [ -f "/app/backend/.env" ]; then
    print_pass "Backend .env exists"
    if grep -q "MONGO_URL" /app/backend/.env; then
        print_pass "MONGO_URL configured"
    else
        print_fail "MONGO_URL not found in .env"
    fi
else
    print_fail "Backend .env not found"
fi

print_check "Checking frontend .env..."
if [ -f "/app/frontend/.env" ]; then
    print_pass "Frontend .env exists"
    if grep -q "REACT_APP_BACKEND_URL" /app/frontend/.env; then
        print_pass "REACT_APP_BACKEND_URL configured"
    else
        print_fail "REACT_APP_BACKEND_URL not found in .env"
    fi
else
    print_fail "Frontend .env not found"
fi

print_check "Checking requirements.txt..."
if [ -f "/app/backend/requirements.txt" ]; then
    print_pass "requirements.txt exists"
else
    print_warn "requirements.txt not found"
fi

print_check "Checking package.json..."
if [ -f "/app/frontend/package.json" ]; then
    print_pass "package.json exists"
else
    print_fail "package.json not found"
fi

# Check Python Dependencies
echo -e "\n${BLUE}=== Python Dependencies ===${NC}\n"

print_check "Checking Python virtual environment..."
if [ -d "/app/.venv" ] || [ -d "/root/.venv" ]; then
    print_pass "Python virtual environment exists"
else
    print_warn "Python virtual environment not found"
fi

print_check "Checking key Python packages..."
if python3 -c "import fastapi" 2>/dev/null; then
    print_pass "fastapi installed"
else
    print_warn "fastapi not installed"
fi

if python3 -c "import chromadb" 2>/dev/null; then
    print_pass "chromadb installed"
else
    print_warn "chromadb not installed"
fi

if python3 -c "import sentence_transformers" 2>/dev/null; then
    print_pass "sentence-transformers installed"
else
    print_warn "sentence-transformers not installed"
fi

# Check Frontend Dependencies
echo -e "\n${BLUE}=== Frontend Dependencies ===${NC}\n"

print_check "Checking node_modules..."
if [ -d "/app/frontend/node_modules" ]; then
    print_pass "node_modules directory exists"
else
    print_warn "node_modules not found - run: cd frontend && yarn install"
fi

# Check Services
echo -e "\n${BLUE}=== Services Status ===${NC}\n"

print_check "Checking MongoDB service..."
if pgrep -x "mongod" > /dev/null; then
    print_pass "MongoDB is running"
elif systemctl is-active --quiet mongod 2>/dev/null; then
    print_pass "MongoDB is running (systemd)"
else
    print_warn "MongoDB is not running"
fi

print_check "Checking backend service..."
if pgrep -f "uvicorn.*server:app" > /dev/null; then
    print_pass "Backend service is running"
else
    print_warn "Backend service is not running"
fi

print_check "Checking frontend service..."
if pgrep -f "react-scripts start\|craco start" > /dev/null; then
    print_pass "Frontend service is running"
else
    print_warn "Frontend service is not running"
fi

# Check API Endpoints
echo -e "\n${BLUE}=== API Connectivity ===${NC}\n"

print_check "Checking backend API..."
BACKEND_RESPONSE=$(curl -s http://localhost:8001/api/ 2>/dev/null || echo "failed")
if [[ $BACKEND_RESPONSE == *"RAG Platform API"* ]]; then
    print_pass "Backend API is responding"
else
    print_warn "Backend API is not responding (may still be starting up)"
fi

print_check "Checking frontend..."
FRONTEND_RESPONSE=$(curl -s http://localhost:3000 2>/dev/null | head -c 50 || echo "failed")
if [[ $FRONTEND_RESPONSE == *"<!DOCTYPE"* ]] || [[ $FRONTEND_RESPONSE != "failed" ]]; then
    print_pass "Frontend is accessible"
else
    print_warn "Frontend is not accessible (may still be starting up)"
fi

# Final Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}  Verification Summary${NC}"
echo -e "${BLUE}========================================${NC}\n"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Your setup is ready.${NC}\n"
    echo -e "Access the platform at: ${GREEN}http://localhost:3000${NC}\n"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Setup mostly complete with $WARNINGS warning(s).${NC}\n"
    echo -e "The platform should work, but some features may be limited.\n"
    echo -e "Access the platform at: ${GREEN}http://localhost:3000${NC}\n"
    exit 0
else
    echo -e "${RED}❌ Found $ERRORS error(s) and $WARNINGS warning(s).${NC}\n"
    echo -e "Please address the errors above before using the platform.\n"
    echo -e "Run ${YELLOW}./run.sh${NC} to set up missing components.\n"
    exit 1
fi
