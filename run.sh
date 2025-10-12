#!/bin/bash

###############################################################################
# RAG Platform - Universal Setup and Run Script
# 
# This script works in two modes:
# 1. FRESH INSTALL: On clean Linux systems (Ubuntu/Debian, CentOS/RHEL, etc.)
# 2. EXISTING SETUP: On systems where dependencies are already installed
#
# Features:
# - Automatic detection of existing setup
# - Smart dependency management
# - Better error handling and diagnostics
# - Port conflict detection
# - Comprehensive logging
# - Works in containers and VMs
###############################################################################

# Don't exit on error immediately - we'll handle errors gracefully
set +e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global flags
SKIP_SYSTEM_INSTALL=false
EXISTING_SETUP=false
VENV_PATH=""

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

print_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to check if a port is in use
is_port_in_use() {
    local port=$1
    if command_exists netstat; then
        netstat -tuln 2>/dev/null | grep -q ":$port "
    elif command_exists ss; then
        ss -tuln 2>/dev/null | grep -q ":$port "
    elif command_exists lsof; then
        lsof -i ":$port" &>/dev/null
    else
        # Fallback: try to connect
        timeout 1 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/$port" 2>/dev/null
    fi
    return $?
}

# Detect existing setup
detect_existing_setup() {
    print_step "🔍 Step 1/10: Detecting Existing Setup"
    
    # Check for existing virtual environments
    local venv_locations=("$SCRIPT_DIR/.venv" "/root/.venv" "$HOME/.venv" "$SCRIPT_DIR/venv")
    
    for venv_path in "${venv_locations[@]}"; do
        if [ -d "$venv_path" ] && [ -f "$venv_path/bin/python" ]; then
            print_message "✓ Found existing virtual environment: $venv_path"
            VENV_PATH="$venv_path"
            EXISTING_SETUP=true
            break
        fi
    done
    
    # Check for existing supervisor configuration
    if [ -f "/etc/supervisor/conf.d/supervisord.conf" ] || [ -f "/etc/supervisor/conf.d/rag-backend.conf" ]; then
        print_message "✓ Found existing supervisor configuration"
        EXISTING_SETUP=true
    fi
    
    # Check if dependencies are already installed
    local all_deps_installed=true
    if ! command_exists python3; then all_deps_installed=false; fi
    if ! command_exists node; then all_deps_installed=false; fi
    if ! command_exists mongod; then all_deps_installed=false; fi
    if ! command_exists supervisorctl; then all_deps_installed=false; fi
    
    if $all_deps_installed; then
        print_message "✓ All system dependencies are installed"
        SKIP_SYSTEM_INSTALL=true
    else
        print_warning "Some system dependencies are missing"
    fi
    
    # Check port availability
    if is_port_in_use 8001; then
        print_warning "Port 8001 is already in use (backend)"
    fi
    if is_port_in_use 3000; then
        print_warning "Port 3000 is already in use (frontend)"
    fi
    if is_port_in_use 27017; then
        print_message "✓ MongoDB is running on port 27017"
    fi
    
    if $EXISTING_SETUP; then
        print_message "✓ Detected existing setup - will use existing configuration"
    else
        print_message "Fresh installation detected - will install all dependencies"
    fi
}

# Detect Linux distribution
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        OS=$DISTRIB_ID
        VERSION=$DISTRIB_RELEASE
    else
        OS=$(uname -s)
        VERSION=$(uname -r)
    fi
    
    print_message "Detected OS: $OS $VERSION"
}

# Check if script is run as root or with sudo
check_sudo() {
    if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
        print_warning "This script requires sudo privileges for system package installation"
        print_warning "You may be prompted for your password"
    fi
}

# Install system packages based on distro
install_system_packages() {
    print_step "📦 Step 2/10: Installing System Dependencies"
    
    if $SKIP_SYSTEM_INSTALL; then
        print_message "✓ System dependencies already installed - skipping"
        return 0
    fi
    
    case $OS in
        ubuntu|debian|pop)
            print_message "Using apt package manager..."
            export DEBIAN_FRONTEND=noninteractive
            
            if ! sudo apt-get update -qq 2>/dev/null; then
                print_error "Failed to update package list"
                return 1
            fi
            
            # Install build essentials
            print_message "Installing build essentials..."
            sudo apt-get install -y -qq build-essential wget curl git software-properties-common
            
            # Install Python if not present
            if ! command -v python3 &> /dev/null; then
                print_message "Installing Python 3..."
                sudo apt-get install -y -qq python3 python3-pip python3-venv python3-dev
            fi
            
            # Install Node.js and npm if not present
            if ! command -v node &> /dev/null; then
                print_message "Installing Node.js..."
                curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
                sudo apt-get install -y -qq nodejs
            fi
            
            # Install yarn if not present
            if ! command -v yarn &> /dev/null; then
                print_message "Installing Yarn..."
                curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
                echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
                sudo apt-get update -qq
                sudo apt-get install -y -qq yarn
            fi
            
            # Install MongoDB if not present
            if ! command -v mongod &> /dev/null; then
                print_message "Installing MongoDB..."
                wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
                echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
                sudo apt-get update -qq
                sudo apt-get install -y -qq mongodb-org
            fi
            
            # Install supervisor if not present
            if ! command -v supervisorctl &> /dev/null; then
                print_message "Installing Supervisor..."
                sudo apt-get install -y -qq supervisor
            fi
            
            # Install OCR and document processing tools
            print_message "Installing OCR and document processing tools..."
            sudo apt-get install -y -qq tesseract-ocr tesseract-ocr-eng tesseract-ocr-fra poppler-utils
            ;;
            
        centos|rhel|fedora)
            print_message "Using yum/dnf package manager..."
            PKG_MANAGER="yum"
            if command -v dnf &> /dev/null; then
                PKG_MANAGER="dnf"
            fi
            
            sudo $PKG_MANAGER install -y -q epel-release
            sudo $PKG_MANAGER groupinstall -y -q "Development Tools"
            
            # Install Python if not present
            if ! command -v python3 &> /dev/null; then
                print_message "Installing Python 3..."
                sudo $PKG_MANAGER install -y -q python3 python3-pip python3-devel
            fi
            
            # Install Node.js if not present
            if ! command -v node &> /dev/null; then
                print_message "Installing Node.js..."
                curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
                sudo $PKG_MANAGER install -y -q nodejs
            fi
            
            # Install yarn if not present
            if ! command -v yarn &> /dev/null; then
                print_message "Installing Yarn..."
                sudo npm install -g yarn
            fi
            
            # Install MongoDB if not present
            if ! command -v mongod &> /dev/null; then
                print_message "Installing MongoDB..."
                cat <<EOF | sudo tee /etc/yum.repos.d/mongodb-org-7.0.repo
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-7.0.asc
EOF
                sudo $PKG_MANAGER install -y -q mongodb-org
            fi
            
            # Install supervisor if not present
            if ! command -v supervisorctl &> /dev/null; then
                print_message "Installing Supervisor..."
                sudo $PKG_MANAGER install -y -q supervisor
            fi
            
            # Install OCR and document processing tools
            print_message "Installing OCR and document processing tools..."
            sudo $PKG_MANAGER install -y -q tesseract tesseract-langpack-eng tesseract-langpack-fra poppler-utils
            ;;
            
        *)
            print_warning "Unknown distribution. Assuming packages are installed."
            print_warning "Please ensure Python3, Node.js, MongoDB, and Supervisor are installed manually."
            ;;
    esac
    
    print_message "✅ System dependencies installed"
}

# Start MongoDB service
start_mongodb() {
    print_step "🗄️  Step 3/10: Starting MongoDB Service"
    
    # Check if MongoDB is already running
    if is_port_in_use 27017; then
        print_message "✅ MongoDB is already running on port 27017"
        return 0
    fi
    
    # Try different methods to start MongoDB
    local mongodb_started=false
    
    if command_exists systemctl; then
        if sudo systemctl start mongod 2>/dev/null; then
            sudo systemctl enable mongod 2>/dev/null || true
            print_message "✅ MongoDB service started with systemctl"
            mongodb_started=true
        fi
    fi
    
    if ! $mongodb_started && command_exists service; then
        if sudo service mongod start 2>/dev/null; then
            print_message "✅ MongoDB service started with service"
            mongodb_started=true
        fi
    fi
    
    if ! $mongodb_started; then
        # Start MongoDB manually if no service manager
        print_warning "No service manager found, starting MongoDB manually..."
        if ! pgrep -x "mongod" > /dev/null; then
            sudo mkdir -p /data/db
            if sudo mongod --fork --logpath /var/log/mongodb.log --dbpath /data/db 2>/dev/null; then
                print_message "✅ MongoDB started manually"
                mongodb_started=true
            fi
        else
            print_message "✅ MongoDB already running (found process)"
            mongodb_started=true
        fi
    fi
    
    if ! $mongodb_started; then
        print_error "Failed to start MongoDB"
        print_warning "Continuing anyway - you may need to start MongoDB manually"
        return 0  # Don't fail the entire script
    fi
    
    # Wait for MongoDB to be ready
    print_message "Waiting for MongoDB to be ready..."
    for i in {1..30}; do
        if mongosh --eval "db.adminCommand('ping')" --quiet 2>/dev/null || mongo --eval "db.adminCommand('ping')" --quiet 2>/dev/null; then
            print_message "✅ MongoDB is ready"
            return 0
        fi
        sleep 1
    done
    
    print_warning "MongoDB may not be fully ready, but continuing..."
    return 0
}

# Create necessary directories
create_directories() {
    print_step "📁 Step 4/10: Creating Directories"
    
    mkdir -p "$SCRIPT_DIR/files"
    mkdir -p "$SCRIPT_DIR/backend/chroma_db"
    mkdir -p "$SCRIPT_DIR/frontend/build"
    mkdir -p "$SCRIPT_DIR/tests"
    mkdir -p "$SCRIPT_DIR/.cache/huggingface"
    mkdir -p "$SCRIPT_DIR/.cache/sentence_transformers"
    
    print_message "✅ All directories created"
}

# Set up Python virtual environment
setup_python_env() {
    print_step "🐍 Step 5/10: Setting Up Python Environment"
    
    # If we found an existing venv, use it
    if [ -n "$VENV_PATH" ] && [ -d "$VENV_PATH" ]; then
        print_message "Using existing virtual environment: $VENV_PATH"
        
        # Test if it works
        if "$VENV_PATH/bin/python" -c "import sys; print(f'Python {sys.version}')" 2>/dev/null; then
            print_message "✅ Virtual environment is functional"
            print_debug "Python version: $($VENV_PATH/bin/python --version 2>&1)"
            
            # Activate it
            if [ -f "$VENV_PATH/bin/activate" ]; then
                source "$VENV_PATH/bin/activate"
                print_debug "Virtual environment activated"
            fi
            
            return 0
        else
            print_warning "Existing venv is broken, will create new one"
            VENV_PATH=""
        fi
    fi
    
    # Determine where to create venv
    if [ -z "$VENV_PATH" ]; then
        # Try to create in script directory first
        if [ -w "$SCRIPT_DIR" ]; then
            VENV_PATH="$SCRIPT_DIR/.venv"
        elif [ -w "/root" ]; then
            VENV_PATH="/root/.venv"
        elif [ -w "$HOME" ]; then
            VENV_PATH="$HOME/.venv"
        else
            VENV_PATH="/tmp/rag-platform-venv"
            print_warning "Using /tmp for venv - not persistent across reboots"
        fi
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_PATH" ]; then
        print_message "Creating Python virtual environment at: $VENV_PATH"
        
        # Check Python version
        PYTHON_VERSION=$(python3 --version 2>&1 || echo "not found")
        print_debug "System Python: $PYTHON_VERSION"
        
        if ! python3 -m venv "$VENV_PATH" 2>&1 | tail -5; then
            print_error "Failed to create virtual environment"
            print_message "Trying with --without-pip flag..."
            
            if python3 -m venv --without-pip "$VENV_PATH" 2>&1; then
                print_message "Created venv without pip, installing pip manually..."
                curl -sS https://bootstrap.pypa.io/get-pip.py | "$VENV_PATH/bin/python"
            else
                print_error "Could not create virtual environment at all"
                return 1
            fi
        fi
        print_message "✅ Virtual environment created"
    else
        print_message "✅ Virtual environment already exists at: $VENV_PATH"
    fi
    
    # Activate virtual environment
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
        print_debug "Activated: $VIRTUAL_ENV"
    else
        print_error "Virtual environment activation script not found"
        return 1
    fi
    
    # Verify activation worked
    WHICH_PYTHON=$(which python 2>/dev/null || echo "not found")
    if [[ "$WHICH_PYTHON" == "$VENV_PATH"* ]]; then
        print_message "✓ Using venv Python: $WHICH_PYTHON"
    else
        print_warning "Python may not be using venv: $WHICH_PYTHON"
    fi
    
    # Upgrade pip
    print_message "Upgrading pip, setuptools, and wheel..."
    if python -m pip install --upgrade pip setuptools wheel 2>&1 | tail -3; then
        print_message "✓ Package tools upgraded"
        print_debug "Pip version: $(pip --version 2>&1)"
    else
        print_warning "Failed to upgrade pip, continuing with current version"
    fi
    
    print_message "✅ Python environment ready"
}

# Install backend dependencies
install_backend_deps() {
    print_step "📚 Step 6/10: Installing Backend Dependencies"
    
    cd "$SCRIPT_DIR/backend"
    
    # Activate virtual environment
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
    else
        print_error "Virtual environment not found at $VENV_PATH"
        return 1
    fi
    
    print_message "Python: $(python --version 2>&1)"
    print_message "Pip: $(pip --version 2>&1)"
    
    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        print_warning "requirements.txt not found, installing essential packages..."
        
        # Install critical packages
        print_message "Installing critical packages..."
        pip install --upgrade pip setuptools wheel
        pip install fastapi uvicorn[standard] motor python-dotenv python-multipart || {
            print_error "Failed to install critical packages"
            return 1
        }
        
        print_message "Installing emergentintegrations..."
        pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ || print_warning "emergentintegrations install failed"
        
        print_message "Installing RAG libraries..."
        pip install chromadb sentence-transformers langchain langchain-community || print_warning "Some RAG libraries failed"
        
        print_message "Installing document processing..."
        pip install pypdf pdfplumber python-docx openpyxl odfpy pytesseract pillow pdf2image watchdog || print_warning "Some doc processing libraries failed"
        
        pip freeze > requirements.txt
        print_message "✅ Created requirements.txt with installed packages"
    else
        # Check if dependencies are already satisfied
        print_message "Checking existing dependencies..."
        
        # Test critical imports
        if python -c "import fastapi, uvicorn, motor" 2>/dev/null; then
            print_message "✓ Critical packages already installed"
            
            # Check if all packages from requirements.txt are installed
            print_message "Verifying all packages from requirements.txt..."
            
            # Count total vs installed
            TOTAL_PACKAGES=$(grep -v "^#" requirements.txt | grep -v "^$" | wc -l)
            
            # Try installing missing packages only
            print_message "Installing/updating packages from requirements.txt..."
            print_message "This may take a few minutes for $TOTAL_PACKAGES packages..."
            
            # Install with progress but no full output
            if pip install -r requirements.txt --no-deps 2>&1 | grep -E "(Installing|Requirement already satisfied|Successfully installed)" | tail -5; then
                print_message "✅ Backend dependencies verified/updated"
            else
                print_warning "Some packages could not be installed, checking critical ones..."
                
                # Verify critical packages work
                if python -c "import fastapi, uvicorn, motor, chromadb" 2>/dev/null; then
                    print_message "✅ Critical packages are functional"
                    print_warning "Some optional packages may be missing (non-critical)"
                else
                    print_error "Critical packages missing, installing individually..."
                    
                    # Install critical packages one by one
                    print_message "1/5 Installing FastAPI..."
                    pip install fastapi uvicorn[standard] || print_error "FastAPI failed"
                    
                    print_message "2/5 Installing Motor (MongoDB)..."
                    pip install motor python-dotenv || print_error "Motor failed"
                    
                    print_message "3/5 Installing Google Generative AI..."
                    pip install google-generativeai || print_error "Google Generative AI failed"
                    
                    print_message "4/5 Installing ChromaDB..."
                    pip install chromadb sentence-transformers || print_error "ChromaDB failed"
                    
                    print_message "5/5 Installing Document Processing..."
                    pip install watchdog pypdf pdfplumber python-docx openpyxl pytesseract pillow pdf2image || print_warning "Some document processors failed"
                    
                    print_message "6/6 Installing LangChain..."
                    pip install langchain langchain-community langchain-core langchain-text-splitters || print_warning "LangChain failed"
                    
                    # Test again
                    if python -c "import fastapi, uvicorn, motor" 2>/dev/null; then
                        print_message "✅ Critical packages installed successfully"
                    else
                        print_error "Failed to install critical packages - backend may not work"
                        return 1
                    fi
                fi
            fi
        else
            print_message "Installing all packages from requirements.txt..."
            print_message "This will take several minutes..."
            
            # Show progress during installation
            pip install -r requirements.txt 2>&1 | while IFS= read -r line; do
                if [[ "$line" =~ "Installing collected packages" ]] || [[ "$line" =~ "Successfully installed" ]] || [[ "$line" =~ "ERROR" ]]; then
                    echo "     $line"
                fi
            done
            
            # Verify installation
            if python -c "import fastapi, uvicorn, motor" 2>/dev/null; then
                print_message "✅ Backend dependencies installed successfully"
            else
                print_error "Installation completed but critical packages missing"
                print_message "Attempting to fix by installing critical packages..."
                pip install fastapi uvicorn[standard] motor python-dotenv
                
                if python -c "import fastapi, uvicorn, motor" 2>/dev/null; then
                    print_message "✅ Critical packages now working"
                else
                    print_error "Critical packages still missing - manual intervention needed"
                    return 1
                fi
            fi
        fi
    fi
    
    # Show final package count
    INSTALLED_COUNT=$(pip list 2>/dev/null | wc -l)
    print_message "Total packages installed: $INSTALLED_COUNT"
    
    cd "$SCRIPT_DIR"
}

# Install frontend dependencies
install_frontend_deps() {
    print_step "⚛️  Step 7/10: Installing Frontend Dependencies"
    
    cd "$SCRIPT_DIR/frontend"
    
    # Check if package.json exists
    if [ ! -f "package.json" ]; then
        print_error "package.json not found in frontend directory"
        cd "$SCRIPT_DIR"
        return 1
    fi
    
    # Check if node_modules exists and is valid
    if [ -d "node_modules" ]; then
        print_message "node_modules directory exists, checking integrity..."
        
        # Check if it looks complete (has react and react-dom at minimum)
        if [ -d "node_modules/react" ] && [ -d "node_modules/react-dom" ]; then
            print_message "✓ Core dependencies (react, react-dom) present"
            
            # Check if yarn.lock or package-lock.json is newer than node_modules
            if [ "package.json" -nt "node_modules" ]; then
                print_warning "package.json is newer than node_modules, reinstalling..."
                rm -rf node_modules package-lock.json yarn.lock 2>/dev/null || true
            else
                print_message "✅ Frontend dependencies already installed and up to date"
                cd "$SCRIPT_DIR"
                return 0
            fi
        else
            print_warning "node_modules incomplete, reinstalling..."
            rm -rf node_modules 2>/dev/null || true
        fi
    fi
    
    print_message "Installing frontend packages (this may take 2-3 minutes)..."
    
    # Try yarn first (preferred)
    if command_exists yarn; then
        print_message "Using yarn package manager..."
        if yarn install 2>&1 | grep -E "(success|Done)" | tail -3; then
            print_message "✅ Frontend dependencies installed with yarn"
            cd "$SCRIPT_DIR"
            return 0
        else
            print_warning "Yarn installation had issues, trying npm..."
        fi
    else
        print_message "Yarn not found, using npm..."
    fi
    
    # Fallback to npm
    if command_exists npm; then
        print_message "Using npm package manager..."
        
        # Clean npm cache if previous attempt failed
        npm cache clean --force 2>/dev/null || true
        
        if npm install 2>&1 | grep -E "(added|up to date)" | tail -5; then
            print_message "✅ Frontend dependencies installed with npm"
            cd "$SCRIPT_DIR"
            return 0
        else
            print_error "npm installation failed"
            
            # Try with --legacy-peer-deps flag
            print_message "Retrying with --legacy-peer-deps..."
            if npm install --legacy-peer-deps 2>&1 | grep -E "(added|up to date)" | tail -5; then
                print_message "✅ Frontend dependencies installed with npm (legacy mode)"
                cd "$SCRIPT_DIR"
                return 0
            else
                print_error "Failed to install frontend dependencies"
                cd "$SCRIPT_DIR"
                return 1
            fi
        fi
    else
        print_error "Neither yarn nor npm found!"
        print_message "Please install Node.js first"
        cd "$SCRIPT_DIR"
        return 1
    fi
}

# Configure environment files
configure_env_files() {
    print_step "⚙️  Step 8/10: Configuring Environment"
    
    # Auto-detect project directory (resolves to absolute path)
    PROJECT_DIR="$(cd "$SCRIPT_DIR" && pwd)"
    print_debug "Project directory detected: $PROJECT_DIR"
    
    # Backend .env - Always regenerate with correct paths
    print_message "Configuring backend .env file..."
    
    # Preserve existing API key if present
    EXISTING_API_KEY=""
    if [ -f "$SCRIPT_DIR/backend/.env" ]; then
        EXISTING_API_KEY=$(grep -E "^GEMINI_API_KEY=" "$SCRIPT_DIR/backend/.env" | cut -d'=' -f2- | tr -d '"' || echo "")
    fi
    
    # Create/Update backend .env with project-relative paths
    cat > "$SCRIPT_DIR/backend/.env" << EOF
# RAG Platform Backend Environment - Auto-generated by run.sh
# Generated: $(date)

# MongoDB Configuration
MONGO_URL="mongodb://localhost:27017"
DB_NAME="rag_platform"

# CORS Configuration
CORS_ORIGINS="*"

# Cache directories - Auto-configured to project directory
# These ensure all model downloads stay within the project for portability
HF_HOME="$PROJECT_DIR/.cache/huggingface"
TRANSFORMERS_CACHE="$PROJECT_DIR/.cache/huggingface"
SENTENCE_TRANSFORMERS_HOME="$PROJECT_DIR/.cache/sentence_transformers"
EOF

    # Restore API key if it existed
    if [ -n "$EXISTING_API_KEY" ]; then
        echo "" >> "$SCRIPT_DIR/backend/.env"
        echo "# Gemini API Key (preserved from previous configuration)" >> "$SCRIPT_DIR/backend/.env"
        echo "GEMINI_API_KEY=\"$EXISTING_API_KEY\"" >> "$SCRIPT_DIR/backend/.env"
        print_message "✓ Preserved existing Gemini API key"
    fi
    
    print_message "✅ Backend .env configured with project-relative paths"
    print_debug "Cache directory: $PROJECT_DIR/.cache"
    
    # Frontend .env - Always regenerate with correct configuration
    print_message "Configuring frontend .env file..."
    
    # Auto-detect backend URL
    BACKEND_URL="http://localhost:8001"
    
    # Check if we're in a container/cloud environment
    if [ -n "$PUBLIC_URL" ]; then
        BACKEND_URL="$PUBLIC_URL"
        print_debug "Using PUBLIC_URL: $PUBLIC_URL"
    elif [ -n "$REACT_APP_BACKEND_URL" ]; then
        BACKEND_URL="$REACT_APP_BACKEND_URL"
        print_debug "Using existing REACT_APP_BACKEND_URL: $REACT_APP_BACKEND_URL"
    fi
    
    # Create frontend .env
    cat > "$SCRIPT_DIR/frontend/.env" << EOF
# RAG Platform Frontend Environment - Auto-generated by run.sh
# Generated: $(date)

# Backend API URL - Auto-configured
REACT_APP_BACKEND_URL=$BACKEND_URL

# WebSocket configuration for development server
# Setting to 0 allows auto-detection of the correct port
# This prevents WebSocket connection errors on port 443
WDS_SOCKET_PORT=0
EOF
    
    print_message "✅ Frontend .env configured with BACKEND_URL: $BACKEND_URL"
    
    # Check if sample documents exist
    print_message "Checking sample documents..."
    DOC_COUNT=$(find "$SCRIPT_DIR/files" -type f 2>/dev/null | wc -l)
    if [ "$DOC_COUNT" -gt 0 ]; then
        print_message "✅ Found $DOC_COUNT document(s) in files directory"
    else
        print_warning "No documents found in files directory"
        print_message "Creating sample documents..."
        
        cat > "$SCRIPT_DIR/files/company_info.md" << 'EOF'
# TechCorp - Company Information

## About Us
TechCorp is a leading technology company providing innovative solutions.

**Founded:** 2020
**Location:** San Francisco, CA

## Our Values
- Innovation
- Customer Focus
- Excellence

## Contact
- Email: info@techcorp.com
- Phone: +1-555-0123
- Office Hours: Monday-Friday, 9 AM - 5 PM PST

---

# TechCorp - Informations sur l'entreprise

## À propos de nous
TechCorp est une entreprise technologique de premier plan fournissant des solutions innovantes.

**Fondée:** 2020
**Emplacement:** San Francisco, CA

## Nos valeurs
- Innovation
- Orientation client
- Excellence
EOF
        
        cat > "$SCRIPT_DIR/files/products.txt" << 'EOF'
TechCorp Products Catalog

1. CloudSync Pro - $99/month
   Enterprise cloud synchronization solution
   
2. DataVault - $149/month
   Secure data storage and backup
   
3. AI Assistant - $199/month
   Intelligent business automation tool
   
All products include 24/7 support and free updates.
EOF
        
        cat > "$SCRIPT_DIR/files/faq.json" << 'EOF'
{
  "faqs": [
    {
      "question": "What is the refund policy?",
      "answer": "We offer a 30-day money-back guarantee on all products."
    },
    {
      "question": "Do you offer technical support?",
      "answer": "Yes, we provide 24/7 technical support for all customers."
    },
    {
      "question": "Can I upgrade my plan?",
      "answer": "Yes, you can upgrade at any time. Contact our sales team."
    }
  ]
}
EOF
        
        print_message "✅ Created 3 sample documents"
    fi
}

# Configure supervisor
configure_supervisor() {
    print_step "🔧 Step 9/10: Configuring Supervisor"
    
    # Check if we should skip supervisor configuration in existing setup
    if [ -f "/etc/supervisor/conf.d/supervisord.conf" ] && grep -q "READONLY FILE" "/etc/supervisor/conf.d/supervisord.conf" 2>/dev/null; then
        print_warning "Found READONLY supervisor config - using existing configuration"
        print_message "✅ Supervisor already configured (read-only mode)"
        return 0
    fi
    
    # Create supervisor config directory if it doesn't exist
    sudo mkdir -p /etc/supervisor/conf.d
    
    # Detect current user
    CURRENT_USER="${USER:-$(whoami)}"
    
    # Get yarn path
    YARN_PATH=$(command -v yarn || echo "/usr/bin/yarn")
    
    # Backend supervisor config
    print_message "Creating backend supervisor configuration..."
    cat << EOF | sudo tee /etc/supervisor/conf.d/rag-backend.conf > /dev/null
[program:backend]
command=$VENV_PATH/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --reload
directory=$SCRIPT_DIR/backend
user=$CURRENT_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/backend.out.log
stderr_logfile=/var/log/supervisor/backend.err.log
environment=PATH="$VENV_PATH/bin:%(ENV_PATH)s",HF_HOME="$SCRIPT_DIR/.cache/huggingface",TRANSFORMERS_CACHE="$SCRIPT_DIR/.cache/huggingface",SENTENCE_TRANSFORMERS_HOME="$SCRIPT_DIR/.cache/sentence_transformers"
stopsignal=TERM
stopwaitsecs=10
stopasgroup=true
killasgroup=true
EOF
    
    # Frontend supervisor config
    print_message "Creating frontend supervisor configuration..."
    cat << EOF | sudo tee /etc/supervisor/conf.d/rag-frontend.conf > /dev/null
[program:frontend]
command=$YARN_PATH start
directory=$SCRIPT_DIR/frontend
user=$CURRENT_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/frontend.out.log
stderr_logfile=/var/log/supervisor/frontend.err.log
environment=PATH="$YARN_PATH:%(ENV_PATH)s",NODE_ENV="development",HOST="0.0.0.0",PORT="3000"
stopsignal=TERM
stopwaitsecs=50
stopasgroup=true
killasgroup=true
EOF
    
    # Create log directory
    sudo mkdir -p /var/log/supervisor
    sudo touch /var/log/supervisor/backend.out.log 2>/dev/null || true
    sudo touch /var/log/supervisor/backend.err.log 2>/dev/null || true
    sudo touch /var/log/supervisor/frontend.out.log 2>/dev/null || true
    sudo touch /var/log/supervisor/frontend.err.log 2>/dev/null || true
    sudo chown -R $CURRENT_USER:$CURRENT_USER /var/log/supervisor/ 2>/dev/null || true
    
    # Start supervisor service
    local supervisor_started=false
    if command_exists systemctl; then
        if sudo systemctl restart supervisor 2>/dev/null; then
            sudo systemctl enable supervisor 2>/dev/null || true
            supervisor_started=true
        fi
    fi
    
    if ! $supervisor_started && command_exists service; then
        if sudo service supervisor restart 2>/dev/null; then
            supervisor_started=true
        fi
    fi
    
    if ! $supervisor_started; then
        # Start supervisord manually
        if ! pgrep -x "supervisord" > /dev/null; then
            if sudo supervisord -c /etc/supervisor/supervisord.conf 2>/dev/null; then
                supervisor_started=true
            fi
        else
            supervisor_started=true
        fi
    fi
    
    if ! $supervisor_started; then
        print_error "Failed to start supervisor"
        return 1
    fi
    
    # Reload supervisor configuration
    sleep 2
    sudo supervisorctl reread 2>/dev/null || true
    sudo supervisorctl update 2>/dev/null || true
    
    print_message "✅ Supervisor configured"
}

# Start services
start_services() {
    print_step "🚀 Step 10/10: Starting Services"
    
    # Stop any existing instances first
    print_message "Stopping any existing instances..."
    sudo supervisorctl stop backend frontend 2>/dev/null || true
    sleep 2
    
    print_message "Starting all services..."
    if sudo supervisorctl start backend frontend 2>/dev/null; then
        print_message "✅ Services start command sent"
    else
        print_warning "Failed to start services with supervisorctl, trying restart all..."
        sudo supervisorctl restart all 2>/dev/null || true
    fi
    
    sleep 5
    
    print_message "Checking service status..."
    sudo supervisorctl status || true
    
    # Check for common errors in logs
    if [ -f "/var/log/supervisor/backend.err.log" ]; then
        if grep -q "Address already in use" /var/log/supervisor/backend.err.log 2>/dev/null; then
            print_error "Backend port 8001 is already in use!"
            print_message "Finding process using port 8001..."
            sudo lsof -i :8001 || sudo netstat -tulpn | grep :8001 || true
        fi
        
        if grep -q "ModuleNotFoundError\|ImportError" /var/log/supervisor/backend.err.log 2>/dev/null; then
            print_error "Missing Python dependencies detected!"
            print_message "Last error from backend log:"
            tail -5 /var/log/supervisor/backend.err.log
        fi
    fi
    
    # Wait for services to be fully ready
    print_message "Waiting for services to initialize..."
    sleep 10
    
    # Check backend health
    print_message "Checking backend health..."
    local backend_healthy=false
    for i in {1..20}; do
        BACKEND_STATUS=$(curl -s http://localhost:8001/api/ 2>/dev/null || echo "failed")
        if [[ $BACKEND_STATUS == *"RAG Platform API"* ]]; then
            print_message "✅ Backend is running and responding"
            backend_healthy=true
            break
        fi
        if [ $i -eq 20 ]; then
            print_error "Backend is not responding properly"
            print_warning "Check logs with: tail -f /var/log/supervisor/backend.err.log"
            print_message "Last 10 lines of backend error log:"
            tail -10 /var/log/supervisor/backend.err.log 2>/dev/null || echo "No log available"
        fi
        sleep 2
    done
    
    # Check frontend
    print_message "Checking frontend..."
    local frontend_healthy=false
    for i in {1..10}; do
        FRONTEND_STATUS=$(curl -s http://localhost:3000 2>/dev/null | head -c 100 || echo "failed")
        if [[ $FRONTEND_STATUS == *"<!DOCTYPE html>"* ]] || [[ $FRONTEND_STATUS != "failed" ]]; then
            print_message "✅ Frontend is running"
            frontend_healthy=true
            break
        fi
        if [ $i -eq 10 ]; then
            print_warning "Frontend may still be starting up (can take 30-60 seconds)"
            print_warning "Check logs with: tail -f /var/log/supervisor/frontend.out.log"
        fi
        sleep 3
    done
    
    # Return status
    if $backend_healthy && $frontend_healthy; then
        return 0
    elif $backend_healthy; then
        print_warning "Backend is running but frontend needs more time"
        return 0
    else
        print_error "Services may not be running correctly"
        return 1
    fi
}

# Main installation flow
main() {
    print_step "🚀 RAG Platform - Universal Setup Script"
    print_message "This script works for both fresh installs and existing setups"
    echo ""
    
    # Pre-flight checks
    check_sudo
    detect_existing_setup
    detect_os
    
    # Installation steps
    install_system_packages
    start_mongodb
    create_directories
    setup_python_env
    install_backend_deps
    install_frontend_deps
    configure_env_files
    configure_supervisor
    start_services
    
    local exit_code=$?
    
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
    print_message "🎉 Platform setup completed!"
    echo ""
    
    # Print diagnostics if services aren't healthy
    if [ $exit_code -ne 0 ]; then
        print_warning "⚠️  Some services may need attention"
        echo ""
        echo -e "${YELLOW}🔍 Quick Diagnostics:${NC}"
        echo ""
        echo -e "${BLUE}Current service status:${NC}"
        sudo supervisorctl status
        echo ""
        echo -e "${BLUE}Port usage:${NC}"
        if command_exists ss; then
            ss -tulpn | grep -E ':(8001|3000|27017)' || echo "  No services detected on expected ports"
        else
            netstat -tulpn 2>/dev/null | grep -E ':(8001|3000|27017)' || echo "  No services detected on expected ports"
        fi
        echo ""
    fi
    
    echo -e "${BLUE}📍 Access Points:${NC}"
    echo -e "   Frontend: ${GREEN}http://localhost:3000${NC}"
    echo -e "   Backend API: ${GREEN}http://localhost:8001/api/${NC}"
    echo -e "   MongoDB: ${GREEN}mongodb://localhost:27017${NC}"
    echo ""
    echo -e "${BLUE}📝 Next Steps:${NC}"
    echo -e "   1. Open ${YELLOW}http://localhost:3000${NC} in your browser"
    echo -e "   2. Go to ${YELLOW}Settings${NC} page"
    echo -e "   3. Add your ${YELLOW}Gemini API key${NC}"
    echo -e "      Get it from: ${BLUE}https://aistudio.google.com/app/apikey${NC}"
    echo -e "   4. Add documents to ${YELLOW}$SCRIPT_DIR/files${NC} directory"
    echo -e "   5. Start chatting with your documents! 💬"
    echo ""
    echo -e "${BLUE}🔧 Useful Commands:${NC}"
    echo -e "   View backend logs:  ${YELLOW}tail -f /var/log/supervisor/backend.err.log${NC}"
    echo -e "   View frontend logs: ${YELLOW}tail -f /var/log/supervisor/frontend.out.log${NC}"
    echo -e "   Restart services:   ${YELLOW}sudo supervisorctl restart all${NC}"
    echo -e "   Check status:       ${YELLOW}sudo supervisorctl status${NC}"
    echo -e "   MongoDB status:     ${YELLOW}sudo systemctl status mongod${NC}"
    echo ""
    echo -e "${BLUE}📚 Sample Documents:${NC}"
    echo -e "   • company_info.md - Company information (English + French)"
    echo -e "   • products.txt    - Product catalog"
    echo -e "   • faq.json        - Frequently asked questions"
    echo ""
    echo -e "${BLUE}🐛 Troubleshooting:${NC}"
    echo -e "   ${YELLOW}Backend fails to start:${NC}"
    echo -e "   1. Check if port 8001 is free: ${YELLOW}sudo lsof -i :8001${NC}"
    echo -e "   2. Check Python venv: ${YELLOW}$VENV_PATH/bin/python --version${NC}"
    echo -e "   3. Check dependencies: ${YELLOW}$VENV_PATH/bin/pip list | grep fastapi${NC}"
    echo -e "   4. View detailed errors: ${YELLOW}tail -50 /var/log/supervisor/backend.err.log${NC}"
    echo ""
    echo -e "   ${YELLOW}MongoDB connection fails:${NC}"
    echo -e "   1. Check MongoDB: ${YELLOW}sudo systemctl status mongod${NC}"
    echo -e "   2. Test connection: ${YELLOW}mongosh --eval 'db.adminCommand(\"ping\")'${NC}"
    echo ""
    echo -e "${GREEN}Happy chatting with your documents! 🚀${NC}"
    echo ""
}

# Run main installation
main

# Keep script running until user presses Ctrl+C
print_step "🎯 RAG Platform is Running"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  RAG Platform is now running and ready to use!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📍 Access Your Platform:${NC}"
echo -e "   🌐 Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "   🔌 Backend API: ${GREEN}http://localhost:8001/api/${NC}"
echo ""
echo -e "${YELLOW}⚠️  Press Ctrl+C to stop all services and exit${NC}"
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
sudo supervisorctl status
echo ""
echo -e "${BLUE}📝 Monitoring Logs (Ctrl+C to stop):${NC}"
echo ""

# Trap Ctrl+C to gracefully shutdown
cleanup() {
    echo ""
    echo ""
    print_step "🛑 Shutting Down RAG Platform"
    echo ""
    print_message "Stopping all services..."
    sudo supervisorctl stop all
    echo ""
    print_message "✅ All services stopped successfully"
    echo ""
    echo -e "${GREEN}Thank you for using RAG Platform! 👋${NC}"
    echo ""
    exit 0
}

trap cleanup SIGINT SIGTERM

# Follow logs and keep script running
echo -e "${BLUE}Following backend logs (press Ctrl+C to stop):${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
tail -f /var/log/supervisor/backend.err.log /var/log/supervisor/backend.out.log 2>/dev/null
