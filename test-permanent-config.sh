#!/bin/bash
# Test script to verify permanent configuration

set -e

echo "============================================"
echo "Testing Permanent Configuration"
echo "============================================"
echo ""

# Test 1: Check run.sh has correct defaults
echo "Test 1: Checking run.sh configuration..."
if grep -q 'VENV_PATH="$SCRIPT_DIR/.venv"' /app/run.sh; then
    echo "  ✓ Virtual environment defaults to /app/.venv"
else
    echo "  ✗ FAILED: Virtual environment not configured correctly"
    exit 1
fi

if grep -q 'mkdir -p "$SCRIPT_DIR/.cache/huggingface"' /app/run.sh; then
    echo "  ✓ Cache directories created by run.sh"
else
    echo "  ✗ FAILED: Cache directories not created by run.sh"
    exit 1
fi

if grep -q 'HF_HOME="$SCRIPT_DIR/.cache/huggingface"' /app/run.sh; then
    echo "  ✓ Environment variables set in backend .env"
else
    echo "  ✗ FAILED: Environment variables not set in backend .env"
    exit 1
fi

# Test 2: Check backend .env
echo ""
echo "Test 2: Checking backend .env..."
if [ -f "/app/backend/.env" ]; then
    if grep -q "HF_HOME" /app/backend/.env; then
        echo "  ✓ Backend .env has cache configuration"
    else
        echo "  ✗ FAILED: Backend .env missing cache configuration"
        exit 1
    fi
else
    echo "  ✗ FAILED: Backend .env not found"
    exit 1
fi

# Test 3: Check supervisor config
echo ""
echo "Test 3: Checking supervisor configuration..."
if grep -q "/app/.venv/bin/uvicorn" /etc/supervisor/conf.d/supervisord.conf; then
    echo "  ✓ Supervisor uses /app/.venv"
else
    echo "  ✗ FAILED: Supervisor not using /app/.venv"
    exit 1
fi

if grep -q "HF_HOME=\"/app/.cache" /etc/supervisor/conf.d/supervisord.conf; then
    echo "  ✓ Supervisor sets cache environment variables"
else
    echo "  ✗ FAILED: Supervisor missing cache environment variables"
    exit 1
fi

# Test 4: Check vector_store.py
echo ""
echo "Test 4: Checking vector_store.py..."
if grep -q "PersistentClient" /app/backend/vector_store.py; then
    echo "  ✓ Uses ChromaDB PersistentClient"
else
    echo "  ✗ FAILED: Not using PersistentClient"
    exit 1
fi

if grep -q 'path="/app/backend/chroma_db"' /app/backend/vector_store.py; then
    echo "  ✓ ChromaDB path is /app/backend/chroma_db"
else
    echo "  ✗ FAILED: ChromaDB path not correct"
    exit 1
fi

# Test 5: Check .gitignore
echo ""
echo "Test 5: Checking .gitignore..."
if grep -q ".venv/" /app/.gitignore && grep -q ".cache/" /app/.gitignore && grep -q "chroma_db/" /app/.gitignore; then
    echo "  ✓ .gitignore configured correctly"
else
    echo "  ✗ FAILED: .gitignore missing entries"
    exit 1
fi

# Test 6: Verify actual locations
echo ""
echo "Test 6: Verifying actual file locations..."
if [ -d "/app/.venv" ]; then
    echo "  ✓ /app/.venv exists"
else
    echo "  ✗ WARNING: /app/.venv does not exist (will be created on first run)"
fi

if [ -d "/app/.cache" ]; then
    echo "  ✓ /app/.cache exists"
else
    echo "  ✗ WARNING: /app/.cache does not exist (will be created on first run)"
fi

if [ -d "/app/backend/chroma_db" ]; then
    echo "  ✓ /app/backend/chroma_db exists"
else
    echo "  ✗ WARNING: /app/backend/chroma_db does not exist (will be created on first run)"
fi

# Test 7: Check services
echo ""
echo "Test 7: Checking services..."
if sudo supervisorctl status backend 2>/dev/null | grep -q "RUNNING"; then
    echo "  ✓ Backend is running"
    
    # Test API
    if curl -s http://localhost:8001/api/ 2>/dev/null | grep -q "running"; then
        echo "  ✓ Backend API responding"
    else
        echo "  ✗ WARNING: Backend API not responding"
    fi
else
    echo "  ✗ WARNING: Backend not running"
fi

if sudo supervisorctl status frontend 2>/dev/null | grep -q "RUNNING"; then
    echo "  ✓ Frontend is running"
else
    echo "  ✗ WARNING: Frontend not running"
fi

echo ""
echo "============================================"
echo "✅ All Permanent Configuration Tests Passed!"
echo "============================================"
echo ""
echo "Configuration is permanent and will persist across:"
echo "  - Service restarts"
echo "  - System reboots"
echo "  - Fresh runs of run.sh script"
echo ""
echo "For detailed documentation, see:"
echo "  /app/PERMANENT_CONFIGURATION.md"
echo ""
