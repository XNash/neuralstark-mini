# RAG Platform - Troubleshooting Guide

## Installation Issues

### Issue: "Failed to install some dependencies from requirements.txt"

**Symptoms:**
```
[RAG Platform] Installing from requirements.txt...
[ERROR] Failed to install some dependencies from requirements.txt
[RAG Platform] Trying to install critical packages individually...
```

**Common Causes:**

1. **Network/Connectivity Issues**
   - Slow or unstable internet connection
   - PyPI mirror temporarily unavailable
   - Corporate firewall blocking package downloads

2. **System Dependencies Missing**
   - Some Python packages need system libraries to compile
   - Common missing dependencies: build-essential, python3-dev, libpq-dev

3. **Python Version Incompatibility**
   - Some packages require specific Python versions
   - Check if you're using Python 3.8 or newer

4. **Disk Space Issues**
   - Insufficient disk space in /tmp or venv directory
   - Package cache taking up space

**Solutions:**

#### Solution 1: Install System Build Tools

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y build-essential python3-dev libpq-dev libssl-dev
```

**CentOS/RHEL:**
```bash
sudo yum groupinstall -y "Development Tools"
sudo yum install -y python3-devel postgresql-devel openssl-devel
```

#### Solution 2: Install Packages in Stages

```bash
cd /app/backend
source /root/.venv/bin/activate  # or /app/.venv

# 1. Upgrade pip and tools
pip install --upgrade pip setuptools wheel

# 2. Install critical packages first
pip install fastapi uvicorn[standard] motor python-dotenv python-multipart

# 3. Install emergentintegrations
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# 4. Install RAG libraries (may take time)
pip install chromadb sentence-transformers

# 5. Install LangChain
pip install langchain langchain-community

# 6. Install document processing
pip install pypdf pdfplumber python-docx openpyxl odfpy pytesseract pillow pdf2image watchdog

# 7. Try the full requirements.txt again
pip install -r requirements.txt
```

#### Solution 3: Use Verbose Mode to See Exact Error

```bash
cd /app/backend
source /root/.venv/bin/activate

# Install with verbose output to see which package fails
pip install -r requirements.txt -v 2>&1 | tee install.log

# Search for ERROR in the log
grep -i "error" install.log
```

#### Solution 4: Skip Problematic Packages

If a specific package keeps failing:

```bash
# Remove the problematic package from requirements.txt temporarily
cd /app/backend
cp requirements.txt requirements.txt.backup

# Remove the failing package line
grep -v "problematic-package-name" requirements.txt.backup > requirements.txt

# Install the rest
pip install -r requirements.txt

# Try installing the problematic package separately with more details
pip install problematic-package-name -v
```

#### Solution 5: Use Pre-built Wheels

Some packages have pre-built wheels that don't require compilation:

```bash
pip install --only-binary :all: -r requirements.txt
```

Or for specific packages:
```bash
pip install --only-binary numpy,scipy,pillow -r requirements.txt
```

### Issue: Frontend Installation Fails

**Symptoms:**
```
[RAG Platform] Installing frontend packages with yarn...
[ERROR] Yarn installation failed, trying npm...
```

**Solutions:**

#### Solution 1: Clear Cache and Retry

```bash
cd /app/frontend

# If using yarn
rm -rf node_modules yarn.lock
yarn cache clean
yarn install

# If using npm
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

#### Solution 2: Use Legacy Peer Dependencies

For npm with React 18:
```bash
cd /app/frontend
npm install --legacy-peer-deps
```

#### Solution 3: Install with More Memory

Node.js might run out of memory:
```bash
cd /app/frontend
export NODE_OPTIONS="--max-old-space-size=4096"
npm install
```

#### Solution 4: Check Node Version

Ensure Node.js 16+ is installed:
```bash
node --version  # Should be v16.x or higher

# If old version, update:
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

## Runtime Issues

### Issue: Backend Won't Start

**Check Logs:**
```bash
tail -50 /var/log/supervisor/backend.err.log
```

**Common Errors and Fixes:**

#### Error: "Address already in use"
```
OSError: [Errno 98] Address already in use
```

**Fix:**
```bash
# Find what's using port 8001
sudo lsof -i :8001
# or
sudo netstat -tulpn | grep 8001

# Kill the process
sudo kill -9 <PID>

# Restart backend
sudo supervisorctl restart backend
```

#### Error: "ModuleNotFoundError: No module named 'fastapi'"

**Fix:**
```bash
# Check which Python supervisor is using
grep "command=" /etc/supervisor/conf.d/rag-backend.conf

# Install missing module in that venv
/path/to/venv/bin/pip install fastapi uvicorn motor

# Restart
sudo supervisorctl restart backend
```

#### Error: "Connection refused to MongoDB"

**Fix:**
```bash
# Check MongoDB status
sudo systemctl status mongod

# If not running, start it
sudo systemctl start mongod

# Test connection
mongosh --eval "db.adminCommand('ping')"

# Restart backend
sudo supervisorctl restart backend
```

### Issue: Frontend Shows Blank Page

**Check Browser Console:**
- Open Developer Tools (F12)
- Look for errors in Console tab
- Check Network tab for failed requests

**Common Issues:**

#### Backend URL Wrong

Check frontend .env:
```bash
cat /app/frontend/.env
# Should show correct REACT_APP_BACKEND_URL
```

Fix:
```bash
# Update with correct URL
echo 'REACT_APP_BACKEND_URL=http://localhost:8001' > /app/frontend/.env

# Restart frontend
sudo supervisorctl restart frontend
```

#### Build Errors

```bash
# Check frontend logs
tail -50 /var/log/supervisor/frontend.out.log

# Look for compilation errors
# Common: missing dependencies, syntax errors
```

### Issue: "spawn error" in Supervisor

**Symptoms:**
```
backend: ERROR (spawn error)
backend: FATAL
```

**Root Cause:** Virtual environment path mismatch

**Fix:**
```bash
# 1. Find your actual venv
ls -la /root/.venv/bin/python
ls -la /app/.venv/bin/python

# 2. Check supervisor config
grep "command=" /etc/supervisor/conf.d/rag-backend.conf

# 3. If paths don't match, update config
sudo nano /etc/supervisor/conf.d/rag-backend.conf
# Change command= to use correct venv path

# 4. Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart backend
```

**Better Fix:** Run the improved `run.sh` which auto-detects the correct path:
```bash
cd /app
./run.sh
```

## Performance Issues

### Issue: Installation is Very Slow

**Causes:**
- Compiling large packages (torch, chromadb, sentence-transformers)
- Slow internet connection
- Limited system resources

**Solutions:**

#### Use Pre-built Binaries
```bash
# Install from specific mirrors with pre-built wheels
pip install --prefer-binary -r requirements.txt
```

#### Increase Timeout
```bash
pip install --timeout 300 -r requirements.txt
```

#### Monitor Progress
```bash
# See what's being installed
pip install -r requirements.txt --progress-bar on
```

### Issue: Services Keep Restarting

**Check:**
```bash
sudo supervisorctl status
# If services show "STARTING" repeatedly, they're crashing
```

**Debug:**
```bash
# Watch logs in real-time
tail -f /var/log/supervisor/backend.err.log

# Look for the error that causes restart
# Common: syntax errors, missing modules, port conflicts
```

## MongoDB Issues

### Issue: MongoDB Won't Start

**Check Status:**
```bash
sudo systemctl status mongod
# Look for error messages
```

**Common Issues:**

#### Port 27017 in Use
```bash
sudo lsof -i :27017
# Kill other process or change MongoDB port
```

#### Permission Issues
```bash
sudo chown -R mongodb:mongodb /var/lib/mongodb
sudo chown -R mongodb:mongodb /var/log/mongodb
sudo systemctl restart mongod
```

#### Disk Space Full
```bash
df -h
# If full, clean up space:
sudo apt-get clean
sudo journalctl --vacuum-time=3d
```

## Network Issues

### Issue: Cannot Access Platform

**Check Services:**
```bash
sudo supervisorctl status
# All should show RUNNING
```

**Test Connectivity:**
```bash
# Backend
curl http://localhost:8001/api/
# Should return: {"message": "RAG Platform API", ...}

# Frontend
curl http://localhost:3000
# Should return HTML
```

**Check Firewall:**
```bash
# Ubuntu/Debian
sudo ufw status
sudo ufw allow 3000
sudo ufw allow 8001

# CentOS/RHEL
sudo firewall-cmd --list-all
sudo firewall-cmd --add-port=3000/tcp --permanent
sudo firewall-cmd --add-port=8001/tcp --permanent
sudo firewall-cmd --reload
```

## Getting Help

### Collect Diagnostic Information

Run the diagnostic script:
```bash
cd /app
./diagnose.sh > diagnostic_output.txt 2>&1
```

### Important Logs to Check

1. **Backend errors:** `/var/log/supervisor/backend.err.log`
2. **Backend output:** `/var/log/supervisor/backend.out.log`
3. **Frontend output:** `/var/log/supervisor/frontend.out.log`
4. **MongoDB logs:** `/var/log/mongodb/mongod.log`
5. **Supervisor logs:** `/var/log/supervisor/supervisord.log`

### System Information to Provide

```bash
# OS and version
cat /etc/os-release

# Python version
python3 --version

# Node version
node --version

# Available disk space
df -h

# Available memory
free -h

# Running processes
ps aux | grep -E "(python|node|mongod)"
```

### Quick Reset

If all else fails, complete reset:

```bash
# Stop all services
sudo supervisorctl stop all

# Remove virtual environment
rm -rf /app/.venv /root/.venv

# Remove node_modules
rm -rf /app/frontend/node_modules

# Run setup again
cd /app
./run.sh
```

## Prevention

### Before Running run.sh

1. **Check system resources:**
   ```bash
   df -h  # At least 5GB free space
   free -h  # At least 2GB RAM
   ```

2. **Update system:**
   ```bash
   sudo apt-get update
   sudo apt-get upgrade
   ```

3. **Install build tools:**
   ```bash
   sudo apt-get install -y build-essential python3-dev
   ```

### Regular Maintenance

1. **Keep dependencies updated:**
   ```bash
   cd /app/backend
   source /root/.venv/bin/activate
   pip list --outdated
   ```

2. **Monitor disk space:**
   ```bash
   df -h
   du -sh /app/.venv
   du -sh /app/frontend/node_modules
   ```

3. **Check logs regularly:**
   ```bash
   ls -lh /var/log/supervisor/
   # Rotate logs if they get too large
   ```

4. **Backup MongoDB:**
   ```bash
   mongodump --out=/backup/mongodb-$(date +%Y%m%d)
   ```

## Still Having Issues?

If none of these solutions work:

1. Run `./diagnose.sh` and review output
2. Check all log files listed above
3. Try the "Quick Reset" procedure
4. Open an issue with:
   - Output from `./diagnose.sh`
   - Relevant log file excerpts
   - Your OS and version
   - Steps you've already tried
