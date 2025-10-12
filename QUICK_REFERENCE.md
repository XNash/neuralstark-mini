# RAG Platform - Quick Reference Card

## 🚀 Getting Started

```bash
# Run the setup script
cd /app
./run.sh

# Run diagnostics
./diagnose.sh
```

## 📊 Service Management

```bash
# Check status
sudo supervisorctl status

# Restart all services
sudo supervisorctl restart all

# Restart individual services
sudo supervisorctl restart backend
sudo supervisorctl restart frontend

# Start/Stop services
sudo supervisorctl start backend
sudo supervisorctl stop backend

# View real-time status
watch -n 2 sudo supervisorctl status
```

## 📝 Logs

```bash
# Backend logs (errors)
tail -f /var/log/supervisor/backend.err.log

# Backend logs (output)
tail -f /var/log/supervisor/backend.out.log

# Frontend logs
tail -f /var/log/supervisor/frontend.out.log

# MongoDB logs
tail -f /var/log/mongodb/mongod.log

# All logs at once
tail -f /var/log/supervisor/*.log

# Search for errors
grep -i error /var/log/supervisor/backend.err.log | tail -20
```

## 🗄️ MongoDB

```bash
# Check status
sudo systemctl status mongod

# Start/Stop/Restart
sudo systemctl start mongod
sudo systemctl stop mongod
sudo systemctl restart mongod

# Connect to MongoDB shell
mongosh

# Test connection
mongosh --eval "db.adminCommand('ping')"

# Show databases
mongosh --eval "show dbs"

# Backup
mongodump --out=/backup/mongodb-$(date +%Y%m%d)

# Restore
mongorestore /backup/mongodb-YYYYMMDD/
```

## 🐍 Python Environment

```bash
# Activate virtual environment
source /root/.venv/bin/activate
# or
source /app/.venv/bin/activate

# Check Python version
python --version

# Check installed packages
pip list

# Check specific package
pip show fastapi

# Install missing package
pip install package-name

# Update package
pip install --upgrade package-name

# Freeze dependencies
pip freeze > requirements.txt
```

## ⚛️ Frontend

```bash
# Install dependencies
cd /app/frontend
yarn install
# or
npm install

# Start development server (manual)
cd /app/frontend
yarn start
# or
npm start

# Check for outdated packages
yarn outdated
# or
npm outdated

# Clear cache
yarn cache clean
# or
npm cache clean --force
```

## 🔍 Debugging

```bash
# Test backend API
curl http://localhost:8001/api/

# Test specific endpoint
curl http://localhost:8001/api/settings

# Test with POST
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# Check port usage
sudo lsof -i :8001
sudo lsof -i :3000
sudo lsof -i :27017

# Alternative port check
sudo netstat -tulpn | grep -E "8001|3000|27017"

# Check disk space
df -h

# Check memory
free -h

# Check CPU
top -bn1 | head -20

# Find process
ps aux | grep python
ps aux | grep node
```

## 🔧 Configuration

```bash
# Backend environment
cat /app/backend/.env
nano /app/backend/.env

# Frontend environment
cat /app/frontend/.env
nano /app/frontend/.env

# Supervisor config (backend)
sudo cat /etc/supervisor/conf.d/rag-backend.conf
sudo nano /etc/supervisor/conf.d/rag-backend.conf

# After config changes, reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
```

## 🧹 Cleanup

```bash
# Clean Python cache
find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Clean pip cache
pip cache purge

# Clean npm/yarn cache
cd /app/frontend
rm -rf node_modules
yarn cache clean

# Clean log files (keep last 100 lines)
for log in /var/log/supervisor/*.log; do
  tail -100 "$log" > "$log.tmp" && mv "$log.tmp" "$log"
done

# Check space before/after
du -sh /app/.venv
du -sh /app/frontend/node_modules
```

## 🔐 Permissions

```bash
# Fix ownership (replace USER with your username)
sudo chown -R USER:USER /app
sudo chown -R USER:USER /var/log/supervisor

# Fix execute permissions
chmod +x /app/run.sh
chmod +x /app/diagnose.sh

# Fix directory permissions
chmod 755 /app
chmod 755 /app/backend
chmod 755 /app/frontend
```

## 🚨 Emergency Fixes

```bash
# Services won't start
sudo supervisorctl stop all
sleep 5
sudo supervisorctl start all

# Backend stuck
sudo supervisorctl stop backend
sudo pkill -9 -f uvicorn
sleep 2
sudo supervisorctl start backend

# Frontend stuck
sudo supervisorctl stop frontend
sudo pkill -9 -f "node.*react-scripts"
sleep 2
sudo supervisorctl start frontend

# MongoDB stuck
sudo systemctl stop mongod
sudo pkill -9 mongod
sleep 2
sudo systemctl start mongod

# Complete reset
sudo supervisorctl stop all
sudo systemctl stop mongod
sleep 5
sudo systemctl start mongod
sleep 5
sudo supervisorctl start all
```

## 📦 Updates

```bash
# Update Python packages
source /root/.venv/bin/activate
pip install --upgrade -r /app/backend/requirements.txt

# Update Node packages
cd /app/frontend
yarn upgrade
# or
npm update

# Update system
sudo apt-get update
sudo apt-get upgrade

# Restart after updates
sudo supervisorctl restart all
```

## 🔄 Reinstall

```bash
# Reinstall backend dependencies
cd /app/backend
rm -rf /root/.venv  # or /app/.venv
python3 -m venv /root/.venv
source /root/.venv/bin/activate
pip install -r requirements.txt

# Reinstall frontend dependencies
cd /app/frontend
rm -rf node_modules package-lock.json yarn.lock
yarn install
# or
npm install

# Use run.sh for automatic reinstall
cd /app
./run.sh
```

## 📞 Health Checks

```bash
# Quick health check
curl -s http://localhost:8001/api/ | jq
curl -s http://localhost:3000 | head -5
mongosh --eval "db.adminCommand('ping')"

# Comprehensive diagnostics
/app/diagnose.sh

# Service status with timing
time curl -s http://localhost:8001/api/

# Watch services
watch -n 1 'sudo supervisorctl status; echo ""; curl -s http://localhost:8001/api/ | jq .'
```

## 🎯 Common Tasks

### Add a Gemini API Key
1. Visit: https://aistudio.google.com/app/apikey
2. Open: http://localhost:3000
3. Go to Settings page
4. Enter API key
5. Click Save

### Add Documents
```bash
# Copy files to watched directory
cp /path/to/document.pdf /app/files/
cp /path/to/document.docx /app/files/

# Files are auto-indexed (check backend logs)
tail -f /var/log/supervisor/backend.out.log
```

### Manual Reindex
```bash
# Via API
curl -X POST http://localhost:8001/api/documents/reindex

# Via UI
# Go to Documents page, click "Reindex Documents"
```

### Check Document Status
```bash
curl http://localhost:8001/api/documents/status | jq
```

### Test Chat
```bash
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What products does TechCorp offer?",
    "session_id": "test-session"
  }' | jq
```

## 📚 More Help

- Full Guide: `cat /app/RUN_SCRIPT_GUIDE.md`
- Troubleshooting: `cat /app/TROUBLESHOOTING.md`
- Installation: `cat /app/INSTALL.md`
- Documentation: `cat /app/README.md`

## 💡 Pro Tips

1. **Bookmark this file** for quick reference
2. **Run diagnostics first** when something doesn't work
3. **Check logs** before asking for help
4. **Keep backups** of MongoDB data
5. **Monitor disk space** regularly
6. **Update packages** monthly
7. **Restart services** after configuration changes
8. **Test with curl** to isolate frontend vs backend issues

---

**Last Updated**: 2024-10-12
**Platform Version**: 2.0
