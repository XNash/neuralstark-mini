# 🚀 RAG Platform - Complete Deployment Guide

This document provides an overview of all deployment methods available for the RAG Platform.

## 📚 Documentation Index

- **[README.md](README.md)** - Project overview, features, and architecture
- **[QUICKSTART.md](QUICKSTART.md)** - Fast setup for existing environments
- **[INSTALL.md](INSTALL.md)** - Detailed installation for clean Linux systems
- **[DOCKER.md](DOCKER.md)** - Docker and Docker Compose deployment
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - This file: deployment overview

## 🎯 Choose Your Deployment Method

### Method 1: Automated Setup (Recommended for Clean Linux)

**Best for:** New Linux servers, VMs, or development environments

**Supported OS:**
- Ubuntu 18.04+ / Debian 10+
- CentOS 7+ / RHEL 7+ / Fedora 30+
- Pop!_OS, Linux Mint, Elementary OS

**Steps:**
```bash
# Clone repository
git clone <repository-url>
cd rag-platform

# Run automated setup
chmod +x run.sh
./run.sh
```

**What it does:**
- Detects your Linux distribution
- Installs Python, Node.js, MongoDB, Supervisor
- Installs OCR tools (Tesseract, Poppler)
- Sets up virtual environments
- Installs all dependencies
- Configures and starts all services
- Creates sample documents

**Time:** ~5-10 minutes

**Documentation:** [INSTALL.md](INSTALL.md)

---

### Method 2: Docker Deployment

**Best for:** Containerized environments, cloud deployments, or isolated testing

**Prerequisites:**
- Docker 20.10+
- Docker Compose 2.0+

**Steps:**
```bash
# Clone repository
git clone <repository-url>
cd rag-platform

# Start with Docker Compose
docker compose up -d

# View logs
docker compose logs -f
```

**What you get:**
- MongoDB container with persistent storage
- Backend container with Python environment
- Frontend container with Node.js
- Automatic networking between containers
- Easy scaling and management

**Time:** ~3-5 minutes

**Documentation:** [DOCKER.md](DOCKER.md)

---

### Method 3: Manual Installation

**Best for:** Custom environments, specific configurations, or learning

**Prerequisites:**
- Python 3.8+
- Node.js 20.x
- MongoDB 7.0
- Supervisor

**Steps:**
See the "Manual Installation" section in [INSTALL.md](INSTALL.md)

**Time:** ~15-30 minutes

---

### Method 4: Kubernetes Deployment

**Best for:** Production environments, high availability, auto-scaling

**Prerequisites:**
- Kubernetes cluster
- kubectl configured
- Helm (optional)

**Status:** Documentation coming soon

---

## 🔍 Verification

After deployment with any method, verify your setup:

```bash
chmod +x verify-setup.sh
./verify-setup.sh
```

Expected output:
```
✅ All checks passed! Your setup is ready.
Access the platform at: http://localhost:3000
```

## 🌐 Access Points

After successful deployment:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | `http://localhost:3000` | Web interface |
| Backend API | `http://localhost:8001/api/` | REST API |
| API Docs | `http://localhost:8001/docs` | Interactive API documentation |
| MongoDB | `mongodb://localhost:27017` | Database (internal) |

## ⚙️ Initial Configuration

### 1. Configure Gemini API Key

**Required for chat functionality**

1. Get API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Open frontend at `http://localhost:3000`
3. Go to **Settings** page
4. Enter your API key
5. Click **Save API Key**

### 2. Add Documents

Place documents in the `/files` directory (or `./files` for Docker):

```bash
# Native installation
cp /path/to/document.pdf /app/files/

# Docker installation
cp /path/to/document.pdf ./files/
```

**Supported formats:**
- PDF (with OCR)
- Word (.doc, .docx)
- Excel (.xls, .xlsx)
- Text (.txt, .md)
- JSON, CSV
- OpenDocument (.odt)

### 3. Verify Indexing

Check document status:
1. Go to **Settings** page
2. View **Document Status** section
3. Wait for indexing (5-10 seconds per document)
4. Trigger manual reindex if needed

## 🛠️ Management Commands

### Native Installation

```bash
# Service management
sudo supervisorctl status              # Check status
sudo supervisorctl restart all         # Restart all services
sudo supervisorctl restart backend     # Restart backend only
sudo supervisorctl restart frontend    # Restart frontend only

# Logs
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/frontend.out.log

# MongoDB
sudo systemctl status mongod
sudo systemctl restart mongod
```

### Docker Deployment

```bash
# Service management
docker compose ps                      # Check status
docker compose restart                 # Restart all services
docker compose restart backend         # Restart backend only
docker compose restart frontend        # Restart frontend only

# Logs
docker compose logs -f                 # All logs
docker compose logs -f backend         # Backend logs only
docker compose logs -f frontend        # Frontend logs only

# Stop/start
docker compose stop                    # Stop services
docker compose start                   # Start services
docker compose down                    # Stop and remove containers
docker compose up -d                   # Start in detached mode
```

## 📊 Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8001/api/

# Document status
curl http://localhost:8001/api/documents/status

# Frontend
curl http://localhost:3000
```

### Resource Usage

**Native:**
```bash
# CPU and memory
top -b -n 1 | grep -E "(python|node)"

# Disk usage
df -h /app
du -sh /app/backend/chroma_db
```

**Docker:**
```bash
# Container stats
docker stats

# Disk usage
docker system df
```

## 🔄 Updates

### Update Application

**Native installation:**
```bash
cd /app
git pull origin main
./run.sh  # Reinstall dependencies
sudo supervisorctl restart all
```

**Docker deployment:**
```bash
cd rag-platform
git pull origin main
docker compose up -d --build
```

### Update Dependencies Only

**Backend:**
```bash
# Native
source .venv/bin/activate
pip install -r backend/requirements.txt
sudo supervisorctl restart backend

# Docker
docker compose up -d --build backend
```

**Frontend:**
```bash
# Native
cd frontend
yarn install
sudo supervisorctl restart frontend

# Docker
docker compose up -d --build frontend
```

## 🔐 Production Considerations

### Security

1. **API Keys:** Never commit `.env` files
2. **MongoDB:** Set authentication
   ```bash
   MONGO_URL="mongodb://username:password@localhost:27017"
   ```
3. **CORS:** Restrict origins
   ```bash
   CORS_ORIGINS="https://yourdomain.com"
   ```
4. **HTTPS:** Use reverse proxy (nginx/Apache)
5. **Firewall:** Restrict MongoDB port (27017)

### Performance

1. **Resources:** Allocate adequate CPU/RAM
   - Minimum: 2 CPU, 4GB RAM
   - Recommended: 4 CPU, 8GB RAM

2. **MongoDB:** Enable indexes and monitoring

3. **ChromaDB:** Regular cleanup of old data

4. **Document Processing:** Limit file sizes

### Backup

**MongoDB:**
```bash
# Native
mongodump --out /backup/mongodb-$(date +%Y%m%d)

# Docker
docker compose exec mongodb mongodump --out /backup
```

**ChromaDB:**
```bash
# Native
tar czf chroma-backup-$(date +%Y%m%d).tar.gz /app/backend/chroma_db

# Docker
docker run --rm -v rag_chroma_data:/data -v $(pwd):/backup ubuntu \
  tar czf /backup/chroma-backup-$(date +%Y%m%d).tar.gz -C /data .
```

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution | Documentation |
|-------|----------|---------------|
| Services won't start | Check logs, verify dependencies | [INSTALL.md](INSTALL.md#troubleshooting) |
| MongoDB connection failed | Verify MongoDB is running | [INSTALL.md](INSTALL.md#mongodb-not-starting) |
| Documents not indexing | Check file permissions, trigger reindex | [README.md](README.md#troubleshooting) |
| Frontend build errors | Clear cache, reinstall node_modules | [DOCKER.md](DOCKER.md#frontend-build-errors) |
| Docker issues | Check logs, prune system | [DOCKER.md](DOCKER.md#troubleshooting) |

### Getting Help

1. **Run verification script:**
   ```bash
   ./verify-setup.sh
   ```

2. **Check logs:**
   - Native: `/var/log/supervisor/*.log`
   - Docker: `docker compose logs`

3. **Review documentation:**
   - [INSTALL.md](INSTALL.md) - Installation troubleshooting
   - [DOCKER.md](DOCKER.md) - Docker troubleshooting
   - [README.md](README.md) - General troubleshooting

## 📞 Support Resources

- **Project Repository:** [GitHub URL]
- **Documentation:** See index at top of this file
- **Issues:** GitHub Issues page
- **API Documentation:** `http://localhost:8001/docs`

## 🎯 Quick Reference

### Essential Commands

```bash
# Verify setup
./verify-setup.sh

# Start platform (native)
./run.sh

# Start platform (Docker)
docker compose up -d

# Check status
sudo supervisorctl status          # Native
docker compose ps                  # Docker

# View logs
tail -f /var/log/supervisor/*.log  # Native
docker compose logs -f             # Docker

# Restart services
sudo supervisorctl restart all     # Native
docker compose restart             # Docker

# Stop platform
sudo supervisorctl stop all        # Native
docker compose down                # Docker
```

### Essential URLs

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8001/api/`
- API Docs: `http://localhost:8001/docs`

### Essential Files

- Configuration: `/app/backend/.env`, `/app/frontend/.env`
- Documents: `/app/files/`
- Logs: `/var/log/supervisor/` (native)
- Data: `/app/backend/chroma_db/`

## 🎉 Next Steps

After successful deployment:

1. ✅ Configure Gemini API key
2. ✅ Add your documents to `/files` directory
3. ✅ Wait for automatic indexing
4. ✅ Start chatting with your documents!
5. ✅ Explore multilingual support (English, French)
6. ✅ Check out the API documentation

---

**Built with ❤️ for seamless deployment on any platform**
