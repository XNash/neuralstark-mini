#!/bin/bash
# NeuralStark - Configuration Verification Script
# This script verifies that all configurations are correct

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "NeuralStark Configuration Verification"
echo "========================================"
echo ""

# Check 1: Virtual Environment Location
echo -n "✓ Virtual environment location: "
if [ -d "/app/.venv" ]; then
    echo -e "${GREEN}/app/.venv ✓${NC}"
else
    echo -e "${RED}/app/.venv NOT FOUND${NC}"
    exit 1
fi

# Check 2: Cache Directories
echo -n "✓ HuggingFace cache: "
if [ -d "/app/.cache/huggingface" ]; then
    SIZE=$(du -sh /app/.cache/huggingface 2>/dev/null | cut -f1)
    echo -e "${GREEN}/app/.cache/huggingface ($SIZE) ✓${NC}"
else
    echo -e "${YELLOW}/app/.cache/huggingface (will be created on first run)${NC}"
fi

echo -n "✓ Sentence Transformers cache: "
if [ -d "/app/.cache/sentence_transformers" ]; then
    SIZE=$(du -sh /app/.cache/sentence_transformers 2>/dev/null | cut -f1)
    echo -e "${GREEN}/app/.cache/sentence_transformers ($SIZE) ✓${NC}"
else
    echo -e "${YELLOW}/app/.cache/sentence_transformers (will be created on first run)${NC}"
fi

# Check 3: ChromaDB Location
echo -n "✓ ChromaDB location: "
if [ -d "/app/backend/chroma_db" ]; then
    SIZE=$(du -sh /app/backend/chroma_db 2>/dev/null | cut -f1)
    echo -e "${GREEN}/app/backend/chroma_db ($SIZE) ✓${NC}"
else
    echo -e "${YELLOW}/app/backend/chroma_db (will be created on first run)${NC}"
fi

# Check 4: Backend .env Configuration
echo -n "✓ Backend .env cache config: "
if grep -q "HF_HOME" /app/backend/.env 2>/dev/null; then
    echo -e "${GREEN}Configured ✓${NC}"
else
    echo -e "${RED}MISSING${NC}"
    exit 1
fi

# Check 5: Supervisor Configuration
echo -n "✓ Supervisor backend config: "
if grep -q "/app/.venv" /etc/supervisor/conf.d/supervisord.conf 2>/dev/null; then
    echo -e "${GREEN}Uses /app/.venv ✓${NC}"
else
    echo -e "${RED}NOT CONFIGURED${NC}"
    exit 1
fi

echo -n "✓ Supervisor cache env vars: "
if grep -q "HF_HOME" /etc/supervisor/conf.d/supervisord.conf 2>/dev/null; then
    echo -e "${GREEN}Configured ✓${NC}"
else
    echo -e "${RED}MISSING${NC}"
    exit 1
fi

# Check 6: Services Status
echo ""
echo "Service Status:"
echo "---------------"
sudo supervisorctl status 2>/dev/null | grep -E "(backend|frontend|mongodb)" || echo "Services not running"

# Check 7: Backend Health
echo ""
echo -n "✓ Backend API: "
if curl -s http://localhost:8001/api/ 2>/dev/null | grep -q "running"; then
    echo -e "${GREEN}Responding ✓${NC}"
else
    echo -e "${YELLOW}Not responding (may be starting up)${NC}"
fi

# Check 8: Frontend Health
echo -n "✓ Frontend: "
if curl -s http://localhost:3000 2>/dev/null | grep -q "<!doctype html>"; then
    echo -e "${GREEN}Responding ✓${NC}"
else
    echo -e "${YELLOW}Not responding (may be starting up)${NC}"
fi

# Summary
echo ""
echo "========================================"
echo -e "${GREEN}Configuration Verification Complete!${NC}"
echo "========================================"
echo ""
echo "All configurations are correct."
echo "For detailed information, see: /app/PERMANENT_CONFIGURATION.md"
echo ""
