# Changelog

All notable changes to the RAG Platform project are documented in this file.

## [2.0.0] - Universal Linux Deployment Update

### 🎉 Major Improvements

#### Universal Installation Support
- **Enhanced `run.sh` script** that works on any clean Linux environment
  - Automatic Linux distribution detection (Ubuntu, Debian, CentOS, RHEL, Fedora)
  - Automatic installation of all system dependencies
  - Python, Node.js, MongoDB, and Supervisor auto-installation
  - Smart package manager detection (apt, yum, dnf)
  - Virtual environment setup and management
  - Comprehensive error handling and user-friendly output
  - Service health checks and verification

#### Docker Support
- **Complete Docker deployment** with Docker Compose
  - Multi-container setup (MongoDB, Backend, Frontend)
  - Persistent volume configuration
  - Health checks for all services
  - Development and production Dockerfiles
  - Optimized .dockerignore files
  - Container networking and port mapping
  - Easy scaling and management

#### Enhanced Documentation
- **[INSTALL.md](INSTALL.md)** - Comprehensive installation guide
  - Step-by-step manual installation instructions
  - OS-specific installation commands
  - Detailed troubleshooting section
  - Security and configuration guidelines
  
- **[DOCKER.md](DOCKER.md)** - Complete Docker deployment guide
  - Quick start with Docker Compose
  - Manual Docker setup instructions
  - Production deployment best practices
  - Container management and monitoring
  - Backup and restore procedures
  
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Unified deployment overview
  - Comparison of all deployment methods
  - Quick reference commands
  - Management and monitoring guidelines
  - Production considerations
  
- **[QUICKSTART.md](QUICKSTART.md)** - Updated quick start guide
  - Enhanced with universal setup information
  - Clear step-by-step instructions
  - Troubleshooting quick reference

#### Verification and Testing
- **New `verify-setup.sh` script** for setup verification
  - Checks all system dependencies
  - Verifies project structure
  - Tests Python and Node.js packages
  - Validates configuration files
  - Checks service status
  - Tests API connectivity
  - Provides detailed health report

#### Configuration Management
- Improved `.env` file handling
- Automatic creation of missing configuration files
- Sample document generation
- Better default values

### 🔧 Technical Improvements

#### Installation Script (`run.sh`)
- OS detection and package manager identification
- Intelligent dependency installation
- MongoDB service configuration and startup
- Supervisor configuration generation
- Python virtual environment management
- Comprehensive error handling
- Progress indicators and colored output
- Service verification and health checks

#### Docker Configuration
- Optimized Dockerfiles for backend and frontend
- Multi-stage builds support
- Volume management for data persistence
- Network configuration between containers
- Health check definitions
- Resource limits and restart policies

#### Project Structure
- Added `.dockerignore` files for optimized builds
- Improved file organization
- Better separation of concerns
- Configuration templates

### 📚 Documentation Improvements

#### New Documentation Files
1. `INSTALL.md` - 450+ lines of installation documentation
2. `DOCKER.md` - 600+ lines of Docker deployment guide
3. `DEPLOYMENT.md` - 400+ lines of deployment overview
4. `CHANGELOG.md` - This file

#### Updated Documentation Files
1. `README.md` - Enhanced with deployment options and verification
2. `QUICKSTART.md` - Updated with universal setup information

#### Documentation Features
- Clear table of contents in all guides
- Code examples with syntax highlighting
- Step-by-step instructions
- Troubleshooting sections
- Quick reference tables
- Command cheat sheets
- Best practices and security considerations

### 🐛 Bug Fixes and Improvements

- Fixed permission issues in automated setup
- Improved MongoDB connection handling
- Better error messages and logging
- Enhanced service startup verification
- Improved supervisor configuration
- Better handling of missing dependencies

### 🔒 Security Enhancements

- Added security considerations documentation
- CORS configuration guidelines
- MongoDB authentication setup instructions
- HTTPS deployment recommendations
- Firewall configuration advice
- Environment variable security

### ⚡ Performance Improvements

- Optimized Docker image sizes
- Improved dependency installation speed
- Better resource allocation guidelines
- Caching strategies for faster builds
- Parallel service startup where possible

### 📦 Dependency Management

- Updated package installation procedures
- Better virtual environment handling
- Improved requirements.txt management
- Yarn lock file support
- Automatic dependency verification

### 🎯 User Experience

- Color-coded terminal output
- Progress indicators during installation
- Clear success/failure messages
- Helpful error messages with solutions
- Comprehensive verification tools
- Easy-to-follow documentation

### 🔄 Compatibility

#### Tested Operating Systems
- ✅ Ubuntu 18.04, 20.04, 22.04, 24.04
- ✅ Debian 10, 11, 12
- ✅ CentOS 7, 8
- ✅ RHEL 7, 8, 9
- ✅ Fedora 30+
- ✅ Pop!_OS 20.04+

#### Docker Support
- ✅ Docker 20.10+
- ✅ Docker Compose 2.0+
- ✅ Docker Swarm
- ✅ Kubernetes (documentation planned)

### 📈 Infrastructure

#### Deployment Methods
1. Native Linux installation (automated)
2. Native Linux installation (manual)
3. Docker Compose
4. Docker manual setup
5. Docker Swarm (documented)
6. Kubernetes (coming soon)

#### Service Management
- Supervisor-based service management
- Docker Compose orchestration
- Health checks and monitoring
- Automatic restart policies
- Log management

### 🛠️ Development Tools

- Setup verification script (`verify-setup.sh`)
- Automated installation script (`run.sh`)
- Docker Compose configuration
- Dockerfiles for all services
- .dockerignore files

### 📝 Configuration Files

#### New Files
- `.dockerignore` (root, backend, frontend)
- `docker-compose.yml`
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `verify-setup.sh`

#### Updated Files
- `run.sh` - Complete rewrite for universal support
- `README.md` - Added deployment sections
- `QUICKSTART.md` - Enhanced with new features
- `.gitignore` - Added Docker and build artifacts

### 🎓 Learning Resources

- Comprehensive installation guides
- Docker best practices
- Production deployment considerations
- Troubleshooting guides
- Quick reference commands
- Security recommendations

### 🚀 Future Enhancements

Planned for future releases:
- Kubernetes deployment manifests
- Helm charts
- Ansible playbooks
- Cloud platform deployment guides (AWS, GCP, Azure)
- Production-optimized builds
- Monitoring and observability integration
- Automated backup solutions
- Multi-region deployment support

## [1.0.0] - Initial Release

### Features
- RAG-based document Q&A system
- FastAPI backend with MongoDB
- React frontend with Tailwind CSS
- ChromaDB vector storage
- Automatic document indexing
- Multilingual support (English, French)
- Chat history and session management
- Multiple document format support
- OCR for scanned PDFs
- Real-time document monitoring

### Supported Document Formats
- PDF (with OCR)
- Word (.doc, .docx)
- Excel (.xls, .xlsx)
- Text (.txt, .md)
- JSON, CSV
- OpenDocument (.odt)

### AI Integration
- Google Gemini 2.5 Flash
- BAAI/bge-base-en-v1.5 embeddings
- RAG architecture for context-aware responses

### Initial Documentation
- README.md with basic setup
- QUICKSTART.md for fast setup
- API documentation

---

## Version History

- **2.0.0** - Universal Linux deployment support, Docker integration, comprehensive documentation
- **1.0.0** - Initial release with core RAG functionality

---

**Note**: This project follows [Semantic Versioning](https://semver.org/).

- **Major version** (X.0.0): Breaking changes or major feature additions
- **Minor version** (x.Y.0): New features, backward compatible
- **Patch version** (x.y.Z): Bug fixes, backward compatible
