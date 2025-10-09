# 🐳 RAG Platform - Docker Deployment Guide

This guide explains how to deploy the RAG Platform using Docker and Docker Compose.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start with Docker Compose](#quick-start-with-docker-compose)
- [Manual Docker Setup](#manual-docker-setup)
- [Configuration](#configuration)
- [Managing the Deployment](#managing-the-deployment)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## 🔧 Prerequisites

### Required Software
- **Docker**: Version 20.10 or later
- **Docker Compose**: Version 2.0 or later

### Installation

#### Ubuntu/Debian
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Add your user to docker group (optional, to avoid sudo)
sudo usermod -aG docker $USER
newgrp docker
```

#### CentOS/RHEL/Fedora
```bash
# Install Docker
sudo dnf install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Verify Installation
```bash
docker --version
docker compose version
```

## 🚀 Quick Start with Docker Compose

### Step 1: Start All Services

From the project root directory:

```bash
# Start all services in detached mode
docker compose up -d

# View logs
docker compose logs -f
```

This will:
- ✅ Start MongoDB container
- ✅ Build and start backend container
- ✅ Build and start frontend container
- ✅ Set up networking between containers
- ✅ Create persistent volumes for data

### Step 2: Verify Services

```bash
# Check status of all services
docker compose ps

# Check backend health
curl http://localhost:8001/api/

# Access frontend
# Open http://localhost:3000 in your browser
```

### Step 3: Configure API Key

1. Open `http://localhost:3000` in your browser
2. Navigate to **Settings** page
3. Enter your Gemini API key
4. Get it from: [Google AI Studio](https://aistudio.google.com/app/apikey)

### Step 4: Add Documents

Documents should be placed in the `/app/files` directory on your host machine:

```bash
# Copy documents to the files directory
cp /path/to/your/document.pdf ./files/

# The backend container will automatically detect and index them
```

### Step 5: Start Chatting!

Visit the Chat page at `http://localhost:3000` and start asking questions about your documents.

## 🔨 Manual Docker Setup

If you prefer to build and run containers manually:

### Build Images

```bash
# Build backend image
cd backend
docker build -t rag-backend:latest .
cd ..

# Build frontend image
cd frontend
docker build -t rag-frontend:latest .
cd ..
```

### Run MongoDB

```bash
docker run -d \
  --name rag-mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:7.0
```

### Run Backend

```bash
docker run -d \
  --name rag-backend \
  -p 8001:8001 \
  -v $(pwd)/backend:/app/backend \
  -v $(pwd)/files:/app/files \
  -e MONGO_URL=mongodb://rag-mongodb:27017 \
  -e DB_NAME=rag_platform \
  -e CORS_ORIGINS=* \
  --link rag-mongodb:mongodb \
  rag-backend:latest
```

### Run Frontend

```bash
docker run -d \
  --name rag-frontend \
  -p 3000:3000 \
  -v $(pwd)/frontend:/app/frontend \
  -e REACT_APP_BACKEND_URL=http://localhost:8001 \
  --link rag-backend:backend \
  rag-frontend:latest
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root for custom configuration:

```bash
# Backend Configuration
MONGO_URL=mongodb://mongodb:27017
DB_NAME=rag_platform
CORS_ORIGINS=*

# Frontend Configuration
REACT_APP_BACKEND_URL=http://localhost:8001
```

Then update `docker-compose.yml` to use this file:

```yaml
services:
  backend:
    env_file:
      - .env
```

### Volumes

The Docker Compose setup uses the following volumes:

- **mongodb_data**: Persistent MongoDB data
- **backend_venv**: Python virtual environment
- **chroma_data**: Vector database storage
- **./files**: Bind mount for document storage

### Ports

Default port mappings:
- **3000**: Frontend (React)
- **8001**: Backend API (FastAPI)
- **27017**: MongoDB

To change ports, edit the `ports` section in `docker-compose.yml`.

## 📊 Managing the Deployment

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mongodb

# Last N lines
docker compose logs --tail=100 backend
```

### Restart Services

```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart backend
```

### Stop Services

```bash
# Stop all services (containers remain)
docker compose stop

# Stop and remove containers
docker compose down

# Stop and remove containers + volumes (WARNING: deletes data)
docker compose down -v
```

### Update Application

```bash
# Pull latest changes (if using git)
git pull

# Rebuild and restart services
docker compose up -d --build

# Or rebuild specific service
docker compose up -d --build backend
```

### Access Container Shell

```bash
# Backend shell
docker compose exec backend bash

# Frontend shell
docker compose exec frontend sh

# MongoDB shell
docker compose exec mongodb mongosh
```

### Scale Services

```bash
# Run multiple backend instances
docker compose up -d --scale backend=3
```

## 🐛 Troubleshooting

### Services Won't Start

**Check logs:**
```bash
docker compose logs backend
docker compose logs frontend
```

**Common issues:**
1. Port already in use:
   ```bash
   # Find what's using the port
   sudo lsof -i :8001
   sudo lsof -i :3000
   ```

2. Insufficient resources:
   ```bash
   # Check Docker resources
   docker stats
   ```

### MongoDB Connection Failed

```bash
# Check if MongoDB is running
docker compose ps mongodb

# Test MongoDB connection
docker compose exec backend python -c "from pymongo import MongoClient; client = MongoClient('mongodb://mongodb:27017'); print(client.server_info())"
```

### Backend API Not Responding

```bash
# Check backend logs
docker compose logs backend | tail -50

# Restart backend
docker compose restart backend

# Check backend health
curl http://localhost:8001/api/
```

### Frontend Build Errors

```bash
# Clear node_modules and rebuild
docker compose down
docker volume rm $(docker volume ls -q | grep node_modules)
docker compose up -d --build frontend
```

### Documents Not Indexing

```bash
# Check if files directory is mounted
docker compose exec backend ls -la /app/files

# Check backend logs for processing errors
docker compose logs backend | grep -i error

# Manually trigger reindexing
curl -X POST http://localhost:8001/api/documents/reindex
```

### Container Disk Space Issues

```bash
# Clean up Docker system
docker system prune -a

# Remove unused volumes
docker volume prune

# Check disk usage
docker system df
```

## 🚀 Production Deployment

### Use Production Build for Frontend

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      - NODE_ENV=production
```

Create `frontend/Dockerfile.prod`:

```dockerfile
FROM node:20-slim as build

WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile
COPY . .
RUN yarn build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Add Nginx Reverse Proxy

Create `nginx.conf`:

```nginx
upstream backend {
    server backend:8001;
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        root /usr/share/nginx/html;
        try_files $uri /index.html;
    }

    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Security Considerations

1. **Use secrets for sensitive data:**
   ```yaml
   services:
     backend:
       secrets:
         - mongo_password
   
   secrets:
     mongo_password:
       file: ./secrets/mongo_password.txt
   ```

2. **Limit resource usage:**
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
   ```

3. **Use health checks:**
   ```yaml
   services:
     backend:
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8001/api/"]
         interval: 30s
         timeout: 10s
         retries: 3
   ```

4. **Enable logging:**
   ```yaml
   services:
     backend:
       logging:
         driver: "json-file"
         options:
           max-size: "10m"
           max-file: "3"
   ```

### Deployment with Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml rag-platform

# Check status
docker stack services rag-platform

# Scale services
docker service scale rag-platform_backend=3
```

### Deployment with Kubernetes

See the included `k8s/` directory for Kubernetes manifests (if available).

## 📈 Monitoring

### Container Stats

```bash
# Real-time stats
docker stats

# One-time snapshot
docker compose ps
```

### Resource Usage

```bash
# Disk usage
docker system df

# Container inspection
docker compose exec backend df -h
```

### Application Metrics

Access metrics endpoints:
- Backend health: `http://localhost:8001/api/`
- Document status: `http://localhost:8001/api/documents/status`

## 🔄 Backup and Restore

### Backup MongoDB Data

```bash
# Create backup
docker compose exec mongodb mongodump --out /backup

# Copy to host
docker cp rag-mongodb:/backup ./mongodb-backup-$(date +%Y%m%d)
```

### Restore MongoDB Data

```bash
# Copy backup to container
docker cp ./mongodb-backup-20240101 rag-mongodb:/backup

# Restore
docker compose exec mongodb mongorestore /backup
```

### Backup Volumes

```bash
# Backup ChromaDB data
docker run --rm \
  -v rag_chroma_data:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/chroma-backup-$(date +%Y%m%d).tar.gz -C /data .
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [RAG Platform README](README.md)
- [Installation Guide](INSTALL.md)

---

**Built with ❤️ for containerized deployments**
