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
    print_step "📦 Step 1/9: Installing System Dependencies"
    
    case $OS in
        ubuntu|debian|pop)
            print_message "Using apt package manager..."
            export DEBIAN_FRONTEND=noninteractive
            sudo apt-get update -qq
            
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
    print_step "🗄️  Step 2/9: Starting MongoDB Service"
    
    # Try different methods to start MongoDB
    if command -v systemctl &> /dev/null; then
        sudo systemctl start mongod 2>/dev/null || true
        sudo systemctl enable mongod 2>/dev/null || true
        print_message "✅ MongoDB service started with systemctl"
    elif command -v service &> /dev/null; then
        sudo service mongod start 2>/dev/null || true
        print_message "✅ MongoDB service started with service"
    else
        # Start MongoDB manually if no service manager
        print_warning "No service manager found, starting MongoDB manually..."
        if ! pgrep -x "mongod" > /dev/null; then
            sudo mkdir -p /data/db
            sudo mongod --fork --logpath /var/log/mongodb.log --dbpath /data/db
            print_message "✅ MongoDB started manually"
        else
            print_message "✅ MongoDB already running"
        fi
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
}

# Create necessary directories
create_directories() {
    print_step "📁 Step 3/9: Creating Directories"
    
    mkdir -p "$SCRIPT_DIR/files"
    mkdir -p "$SCRIPT_DIR/backend/chroma_db"
    mkdir -p "$SCRIPT_DIR/frontend/build"
    mkdir -p "$SCRIPT_DIR/tests"
    
    print_message "✅ All directories created"
}

# Set up Python virtual environment
setup_python_env() {
    print_step "🐍 Step 4/9: Setting Up Python Environment"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$SCRIPT_DIR/.venv" ]; then
        print_message "Creating Python virtual environment..."
        python3 -m venv "$SCRIPT_DIR/.venv"
        print_message "✅ Virtual environment created"
    else
        print_message "✅ Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source "$SCRIPT_DIR/.venv/bin/activate"
    
    # Upgrade pip
    print_message "Upgrading pip..."
    pip install --quiet --upgrade pip setuptools wheel
    
    print_message "✅ Python environment ready"
}

# Install backend dependencies
install_backend_deps() {
    print_step "📚 Step 5/9: Installing Backend Dependencies"
    
    cd "$SCRIPT_DIR/backend"
    
    # Activate virtual environment
    source "$SCRIPT_DIR/.venv/bin/activate"
    
    print_message "Installing emergentintegrations library..."
    pip install --quiet emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
    
    print_message "Installing FastAPI and web server..."
    pip install --quiet fastapi uvicorn[standard] motor python-dotenv python-multipart
    
    print_message "Installing RAG and vector store libraries..."
    pip install --quiet chromadb sentence-transformers langchain langchain-community
    
    print_message "Installing document processing libraries..."
    pip install --quiet pypdf pdfplumber python-docx openpyxl odfpy pytesseract pillow pdf2image
    
    print_message "Installing file monitoring..."
    pip install --quiet watchdog
    
    # Update requirements.txt
    print_message "Updating requirements.txt..."
    pip freeze > requirements.txt
    
    print_message "✅ Backend dependencies installed"
    
    cd "$SCRIPT_DIR"
}

# Install frontend dependencies
install_frontend_deps() {
    print_step "⚛️  Step 6/9: Installing Frontend Dependencies"
    
    cd "$SCRIPT_DIR/frontend"
    
    if [ ! -d "node_modules" ] || [ ! -f "node_modules/.yarn-integrity" ]; then
        print_message "Installing frontend packages with yarn..."
        yarn install --silent
        print_message "✅ Frontend dependencies installed"
    else
        print_message "✅ Frontend dependencies already installed"
    fi
    
    cd "$SCRIPT_DIR"
}

# Configure environment files
configure_env_files() {
    print_step "⚙️  Step 7/9: Configuring Environment"
    
    # Backend .env
    if [ ! -f "$SCRIPT_DIR/backend/.env" ]; then
        print_message "Creating backend .env file..."
        cat > "$SCRIPT_DIR/backend/.env" << EOF
MONGO_URL="mongodb://localhost:27017"
DB_NAME="rag_platform"
CORS_ORIGINS="*"
EOF
        print_message "✅ Backend .env created"
    else
        print_message "✅ Backend .env exists"
    fi
    
    # Frontend .env
    if [ ! -f "$SCRIPT_DIR/frontend/.env" ]; then
        print_message "Creating frontend .env file..."
        # Try to detect the public URL
        if [ -n "$PUBLIC_URL" ]; then
            BACKEND_URL="$PUBLIC_URL"
        else
            BACKEND_URL="http://localhost:8001"
        fi
        
        cat > "$SCRIPT_DIR/frontend/.env" << EOF
REACT_APP_BACKEND_URL=$BACKEND_URL
WDS_SOCKET_PORT=443
EOF
        print_message "✅ Frontend .env created"
    else
        print_message "✅ Frontend .env exists"
    fi
    
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
    print_step "🔧 Step 8/9: Configuring Supervisor"
    
    # Create supervisor config directory if it doesn't exist
    sudo mkdir -p /etc/supervisor/conf.d
    
    # Backend supervisor config
    print_message "Creating backend supervisor configuration..."
    cat << EOF | sudo tee /etc/supervisor/conf.d/rag-backend.conf > /dev/null
[program:backend]
command=$SCRIPT_DIR/.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --reload
directory=$SCRIPT_DIR/backend
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/backend.out.log
stderr_logfile=/var/log/supervisor/backend.err.log
environment=PATH="$SCRIPT_DIR/.venv/bin:%(ENV_PATH)s"
EOF
    
    # Frontend supervisor config
    print_message "Creating frontend supervisor configuration..."
    cat << EOF | sudo tee /etc/supervisor/conf.d/rag-frontend.conf > /dev/null
[program:frontend]
command=/usr/bin/yarn start
directory=$SCRIPT_DIR/frontend
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/frontend.out.log
stderr_logfile=/var/log/supervisor/frontend.err.log
environment=PATH="/usr/bin:%(ENV_PATH)s",NODE_ENV="development"
EOF
    
    # Create log directory
    sudo mkdir -p /var/log/supervisor
    sudo touch /var/log/supervisor/backend.out.log
    sudo touch /var/log/supervisor/backend.err.log
    sudo touch /var/log/supervisor/frontend.out.log
    sudo touch /var/log/supervisor/frontend.err.log
    sudo chown -R $USER:$USER /var/log/supervisor/ 2>/dev/null || true
    
    # Start supervisor service
    if command -v systemctl &> /dev/null; then
        sudo systemctl restart supervisor 2>/dev/null || true
        sudo systemctl enable supervisor 2>/dev/null || true
    elif command -v service &> /dev/null; then
        sudo service supervisor restart 2>/dev/null || true
    else
        # Start supervisord manually
        if ! pgrep -x "supervisord" > /dev/null; then
            sudo supervisord -c /etc/supervisor/supervisord.conf
        fi
    fi
    
    # Reload supervisor configuration
    sleep 2
    sudo supervisorctl reread 2>/dev/null || true
    sudo supervisorctl update 2>/dev/null || true
    
    print_message "✅ Supervisor configured"
}

# Start services
start_services() {
    print_step "🚀 Step 9/9: Starting Services"
    
    print_message "Starting all services..."
    sudo supervisorctl restart all 2>/dev/null || true
    
    sleep 5
    
    print_message "Checking service status..."
    sudo supervisorctl status || true
    
    # Wait for services to be fully ready
    print_message "Waiting for services to initialize..."
    sleep 10
    
    # Check backend health
    print_message "Checking backend health..."
    for i in {1..20}; do
        BACKEND_STATUS=$(curl -s http://localhost:8001/api/ 2>/dev/null || echo "failed")
        if [[ $BACKEND_STATUS == *"RAG Platform API"* ]]; then
            print_message "✅ Backend is running"
            break
        fi
        if [ $i -eq 20 ]; then
            print_error "Backend may not be running properly"
            print_warning "Check logs with: tail -f /var/log/supervisor/backend.err.log"
        fi
        sleep 2
    done
    
    # Check frontend
    print_message "Checking frontend..."
    sleep 5
    for i in {1..10}; do
        FRONTEND_STATUS=$(curl -s http://localhost:3000 2>/dev/null | head -c 100 || echo "failed")
        if [[ $FRONTEND_STATUS == *"<!DOCTYPE html>"* ]] || [[ $FRONTEND_STATUS != "failed" ]]; then
            print_message "✅ Frontend is running"
            break
        fi
        if [ $i -eq 10 ]; then
            print_warning "Frontend may still be starting up"
            print_warning "Check logs with: tail -f /var/log/supervisor/frontend.out.log"
        fi
        sleep 3
    done
}

# Main installation flow
main() {
    print_step "🚀 RAG Platform - Universal Setup for Clean Linux"
    
    # Pre-flight checks
    check_sudo
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
    echo -e "   If services don't start:"
    echo -e "   1. Check MongoDB: ${YELLOW}sudo systemctl status mongod${NC}"
    echo -e "   2. Check supervisor: ${YELLOW}sudo systemctl status supervisor${NC}"
    echo -e "   3. Review logs in: ${YELLOW}/var/log/supervisor/${NC}"
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
