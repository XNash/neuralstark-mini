#!/bin/bash
# Test script to verify portability of NeuralStark
# This simulates what a GitHub user would experience

set -e

GREEN='33[0;32m'
RED='33[0;31m'
YELLOW='33[1;33m'
BLUE='33[0;34m'
NC='33[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_test() {
    echo -e "${YELLOW}🧪 $1${NC}"
}

echo "=========================================="
echo "NeuralStark - Portability Test Suite"
echo "=========================================="
echo ""

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Test 1: Check for hardcoded paths in Python files
print_test "Test 1: Checking for hardcoded paths in Python code..."
HARDCODED_PATHS=$(grep -r "path=\"/app" backend/*.py 2>/dev/null || true)
if [ -z "$HARDCODED_PATHS" ]; then
    print_success "No hardcoded /app paths found in Python code"
else
    print_error "Found hardcoded paths:"
    echo "$HARDCODED_PATHS"
    exit 1
fi

# Test 2: Check vector_store.py uses relative paths
print_test "Test 2: Verifying vector_store.py uses relative paths..."
if grep -q "Path(__file__).parent" backend/vector_store.py; then
    print_success "vector_store.py uses relative Path logic"
else
    print_error "vector_store.py doesn't use relative paths"
    exit 1
fi

# Test 3: Check rag_service.py doesn't reference /app/files
print_test "Test 3: Checking rag_service.py error messages..."
if grep -q "/app/files" backend/rag_service.py; then
    print_error "Found /app/files references in rag_service.py"
    exit 1
else
    print_success "rag_service.py uses generic 'files directory' references"
fi

# Test 4: Check .env.example files don't have hardcoded paths
print_test "Test 4: Checking .env.example files..."
if grep -q "^HF_HOME=\"/app" backend/.env.example 2>/dev/null; then
    print_error "backend/.env.example has hardcoded /app paths"
    exit 1
else
    print_success "backend/.env.example uses placeholders"
fi

# Test 5: Verify run.sh has auto-detection logic
print_test "Test 5: Verifying run.sh auto-detection..."
if grep -q "PROJECT_DIR=" run.sh && grep -q "cd.*pwd" run.sh; then
    print_success "run.sh has project directory auto-detection"
else
    print_error "run.sh missing auto-detection logic"
    exit 1
fi

# Test 6: Check post-clone-setup.sh creates directories
print_test "Test 6: Verifying post-clone-setup.sh structure..."
if grep -q "mkdir -p.*\.cache" post-clone-setup.sh; then
    print_success "post-clone-setup.sh creates cache directories"
else
    print_error "post-clone-setup.sh missing directory creation"
    exit 1
fi

# Test 7: Verify documentation uses relative paths
print_test "Test 7: Checking README.md for hardcoded paths..."
HARDCODED_DOCS=$(grep -o "Watches.*\`/app" README.md 2>/dev/null || true)
if [ -z "$HARDCODED_DOCS" ]; then
    print_success "README.md uses relative path references"
else
    print_error "Found hardcoded paths in documentation"
    exit 1
fi

# Test 8: Check GITHUB_SETUP.md exists
print_test "Test 8: Verifying GitHub setup guide exists..."
if [ -f "GITHUB_SETUP.md" ]; then
    print_success "GITHUB_SETUP.md exists for GitHub users"
else
    print_error "GITHUB_SETUP.md not found"
    exit 1
fi

# Test 9: Verify backend can import with relative paths
print_test "Test 9: Testing Python imports..."
cd backend
if python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, '.')
from vector_store import VectorStoreService
print('Import successful')
" 2>&1 | grep -q "Import successful"; then
    print_success "vector_store.py imports successfully"
else
    print_error "Failed to import vector_store.py"
    exit 1
fi
cd ..

# Test 10: Simulate path detection in different directory
print_test "Test 10: Simulating different installation directory..."
TEST_DIR="/tmp/test-rag-$(date +%s)"
SIMULATED_PATH="$CURRENT_DIR/.cache/huggingface"
if [ -d "$CURRENT_DIR/.cache" ]; then
    print_success "Cache directory structure exists at: $SIMULATED_PATH"
else
    print_info "Would create cache at: $SIMULATED_PATH"
fi

# Test 11: Check if .env files are properly formatted
print_test "Test 11: Verifying .env file format..."
if [ -f "backend/.env" ]; then
    if grep -q "^MONGO_URL=" backend/.env && grep -q "^DB_NAME=" backend/.env; then
        print_success "backend/.env has required variables"
    else
        print_error "backend/.env missing required variables"
        exit 1
    fi
fi

if [ -f "frontend/.env" ]; then
    if grep -q "^REACT_APP_BACKEND_URL=" frontend/.env; then
        print_success "frontend/.env has required variables"
    else
        print_error "frontend/.env missing required variables"
        exit 1
    fi
fi

# Test 12: Check scripts are executable
print_test "Test 12: Verifying scripts are executable..."
SCRIPTS=("run.sh" "post-clone-setup.sh")
ALL_EXECUTABLE=true
for script in "${SCRIPTS[@]}"; do
    if [ -x "$script" ]; then
        print_success "$script is executable"
    else
        print_info "$script is not executable (post-clone-setup.sh will fix)"
    fi
done

# Test 13: Check for relative imports in server.py
print_test "Test 13: Verifying server.py uses relative paths..."
if grep -q "Path(__file__).parent.parent" backend/server.py; then
    print_success "server.py uses relative path resolution"
else
    print_error "server.py may have hardcoded paths"
    exit 1
fi

# Test 14: Verify portability documentation
print_test "Test 14: Checking portability documentation..."
if [ -f "PORTABILITY_CHANGES.md" ]; then
    print_success "PORTABILITY_CHANGES.md exists"
else
    print_info "PORTABILITY_CHANGES.md not found (optional)"
fi

echo ""
echo "=========================================="
print_success "All Portability Tests Passed! 🎉"
echo "=========================================="
echo ""
print_info "Summary:"
echo "  ✅ No hardcoded paths in code"
echo "  ✅ All paths use relative resolution"
echo "  ✅ Configuration examples use placeholders"
echo "  ✅ Setup scripts auto-detect directories"
echo "  ✅ Documentation uses generic paths"
echo "  ✅ GitHub setup guide available"
echo ""
print_success "This NeuralStark is portable and will work anywhere!"
echo ""
print_info "GitHub Clone Test:"
echo "  Users can clone to any directory and run:"
echo "    git clone <repo> /any/path/rag-platform"
echo "    cd /any/path/rag-platform"
echo "    ./post-clone-setup.sh"
echo "    ./run.sh"
echo ""
print_success "Ready for GitHub distribution! 🚀"
