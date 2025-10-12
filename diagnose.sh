#!/bin/bash

###############################################################################
# RAG Platform - Diagnostic Script
# Run this script to diagnose common issues with the platform
###############################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  RAG Platform Diagnostics${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check 1: System dependencies
echo -e "${BLUE}[1/10] Checking System Dependencies${NC}"
echo "-----------------------------------"

check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "  ✅ $1: $(command -v $1)"
        if [ "$1" = "python3" ]; then
            echo "     Version: $(python3 --version 2>&1)"
        elif [ "$1" = "node" ]; then
            echo "     Version: $(node --version 2>&1)"
        elif [ "$1" = "mongod" ]; then
            echo "     Version: $(mongod --version 2>&1 | head -1)"
        fi
    else
        echo -e "  ${RED}❌ $1: Not found${NC}"
    fi
}

check_command python3
check_command node
check_command yarn
check_command mongod
check_command supervisorctl
echo ""

# Check 2: Virtual environments
echo -e "${BLUE}[2/10] Checking Virtual Environments${NC}"
echo "--------------------------------------"
venv_found=false
for venv_path in "$SCRIPT_DIR/.venv" "/root/.venv" "$HOME/.venv"; do
    if [ -d "$venv_path" ]; then
        echo -e "  ✅ Found: $venv_path"
        if [ -f "$venv_path/bin/python" ]; then
            echo "     Python: $($venv_path/bin/python --version 2>&1)"
            echo "     Packages: $($venv_path/bin/pip list 2>/dev/null | wc -l) installed"
            venv_found=true
        fi
    fi
done
if [ "$venv_found" = false ]; then
    echo -e "  ${RED}❌ No virtual environment found${NC}"
fi
echo ""

# Check 3: Port availability
echo -e "${BLUE}[3/10] Checking Port Availability${NC}"
echo "-----------------------------------"

check_port() {
    local port=$1
    local service=$2
    if command -v ss &> /dev/null; then
        if ss -tuln 2>/dev/null | grep -q ":$port "; then
            echo -e "  ${YELLOW}⚠️  Port $port ($service): IN USE${NC}"
            ss -tulpn 2>/dev/null | grep ":$port " | head -1
        else
            echo -e "  ✅ Port $port ($service): Available"
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            echo -e "  ${YELLOW}⚠️  Port $port ($service): IN USE${NC}"
            netstat -tulpn 2>/dev/null | grep ":$port " | head -1
        else
            echo -e "  ✅ Port $port ($service): Available"
        fi
    else
        echo -e "  ${YELLOW}⚠️  Cannot check port $port (no ss/netstat)${NC}"
    fi
}

check_port 8001 "Backend"
check_port 3000 "Frontend"
check_port 27017 "MongoDB"
echo ""

# Check 4: MongoDB status
echo -e "${BLUE}[4/10] Checking MongoDB${NC}"
echo "-----------------------"
if pgrep -x mongod > /dev/null; then
    echo -e "  ✅ MongoDB process is running"
    if command -v mongosh &> /dev/null; then
        if mongosh --eval "db.adminCommand('ping')" --quiet 2>/dev/null; then
            echo -e "  ✅ MongoDB is responding to commands"
        else
            echo -e "  ${RED}❌ MongoDB not responding${NC}"
        fi
    elif command -v mongo &> /dev/null; then
        if mongo --eval "db.adminCommand('ping')" --quiet 2>/dev/null; then
            echo -e "  ✅ MongoDB is responding to commands"
        else
            echo -e "  ${RED}❌ MongoDB not responding${NC}"
        fi
    fi
else
    echo -e "  ${RED}❌ MongoDB process not found${NC}"
fi
echo ""

# Check 5: Supervisor status
echo -e "${BLUE}[5/10] Checking Supervisor${NC}"
echo "---------------------------"
if pgrep -x supervisord > /dev/null; then
    echo -e "  ✅ Supervisor is running"
    echo ""
    sudo supervisorctl status 2>/dev/null || echo -e "  ${RED}❌ Cannot get supervisor status${NC}"
else
    echo -e "  ${RED}❌ Supervisor is not running${NC}"
fi
echo ""

# Check 6: Supervisor configuration
echo -e "${BLUE}[6/10] Checking Supervisor Configuration${NC}"
echo "------------------------------------------"
if [ -f "/etc/supervisor/conf.d/rag-backend.conf" ]; then
    echo -e "  ✅ Backend config exists"
    echo "     Command: $(grep "^command=" /etc/supervisor/conf.d/rag-backend.conf)"
elif [ -f "/etc/supervisor/conf.d/supervisord.conf" ]; then
    echo -e "  ✅ Unified config exists (supervisord.conf)"
    echo "     Backend command: $(grep -A5 "\[program:backend\]" /etc/supervisor/conf.d/supervisord.conf | grep "^command=")"
else
    echo -e "  ${RED}❌ No supervisor config found${NC}"
fi
echo ""

# Check 7: Environment files
echo -e "${BLUE}[7/10] Checking Environment Files${NC}"
echo "-----------------------------------"
if [ -f "$SCRIPT_DIR/backend/.env" ]; then
    echo -e "  ✅ Backend .env exists"
    echo "     MONGO_URL: $(grep MONGO_URL $SCRIPT_DIR/backend/.env | cut -d'=' -f2)"
    echo "     DB_NAME: $(grep DB_NAME $SCRIPT_DIR/backend/.env | cut -d'=' -f2)"
else
    echo -e "  ${RED}❌ Backend .env missing${NC}"
fi

if [ -f "$SCRIPT_DIR/frontend/.env" ]; then
    echo -e "  ✅ Frontend .env exists"
    echo "     REACT_APP_BACKEND_URL: $(grep REACT_APP_BACKEND_URL $SCRIPT_DIR/frontend/.env | cut -d'=' -f2)"
else
    echo -e "  ${RED}❌ Frontend .env missing${NC}"
fi
echo ""

# Check 8: Backend health
echo -e "${BLUE}[8/10] Checking Backend Health${NC}"
echo "--------------------------------"
BACKEND_RESPONSE=$(curl -s http://localhost:8001/api/ 2>/dev/null || echo "failed")
if [[ $BACKEND_RESPONSE == *"RAG Platform API"* ]]; then
    echo -e "  ✅ Backend is responding correctly"
    echo "     Response: $BACKEND_RESPONSE"
else
    echo -e "  ${RED}❌ Backend is not responding${NC}"
    if [ -f "/var/log/supervisor/backend.err.log" ]; then
        echo ""
        echo "  Last 10 lines of backend error log:"
        tail -10 /var/log/supervisor/backend.err.log | sed 's/^/     /'
    fi
fi
echo ""

# Check 9: Frontend health
echo -e "${BLUE}[9/10] Checking Frontend Health${NC}"
echo "--------------------------------"
FRONTEND_RESPONSE=$(curl -s http://localhost:3000 2>/dev/null | head -c 100)
if [[ $FRONTEND_RESPONSE == *"<!DOCTYPE html>"* ]]; then
    echo -e "  ✅ Frontend is responding"
else
    echo -e "  ${YELLOW}⚠️  Frontend may still be starting up${NC}"
fi
echo ""

# Check 10: Documents
echo -e "${BLUE}[10/10] Checking Documents${NC}"
echo "---------------------------"
if [ -d "$SCRIPT_DIR/files" ]; then
    DOC_COUNT=$(find "$SCRIPT_DIR/files" -type f 2>/dev/null | wc -l)
    if [ "$DOC_COUNT" -gt 0 ]; then
        echo -e "  ✅ Found $DOC_COUNT document(s) in files directory"
        find "$SCRIPT_DIR/files" -type f -exec basename {} \; | sed 's/^/     - /'
    else
        echo -e "  ${YELLOW}⚠️  No documents in files directory${NC}"
    fi
else
    echo -e "  ${RED}❌ Files directory not found${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Diagnostic Summary${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Collect issues
issues=()

if ! command -v python3 &> /dev/null; then issues+=("Python 3 not installed"); fi
if ! command -v node &> /dev/null; then issues+=("Node.js not installed"); fi
if ! command -v mongod &> /dev/null; then issues+=("MongoDB not installed"); fi
if ! command -v supervisorctl &> /dev/null; then issues+=("Supervisor not installed"); fi
if ! pgrep -x mongod > /dev/null; then issues+=("MongoDB not running"); fi
if ! pgrep -x supervisord > /dev/null; then issues+=("Supervisor not running"); fi
if [[ ! $BACKEND_RESPONSE == *"RAG Platform API"* ]]; then issues+=("Backend not responding"); fi

if [ ${#issues[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Platform appears healthy.${NC}"
    echo ""
    echo "Access your platform at:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - Backend API: http://localhost:8001/api/"
else
    echo -e "${YELLOW}⚠️  Found ${#issues[@]} issue(s):${NC}"
    for issue in "${issues[@]}"; do
        echo "  - $issue"
    done
    echo ""
    echo -e "${BLUE}Recommended Action:${NC}"
    echo "  Run the setup script: ./run.sh"
fi
echo ""
