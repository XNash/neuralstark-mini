/**
 * PM2 Ecosystem Configuration for RAG Platform
 * Cross-platform process management for Windows, Linux, and macOS
 * 
 * Usage:
 *   Start all services: pm2 start ecosystem.config.js
 *   Stop all services: pm2 stop ecosystem.config.js
 *   Restart all services: pm2 restart ecosystem.config.js
 *   View logs: pm2 logs
 *   Monitor: pm2 monit
 *   Status: pm2 status
 */

const path = require('path');
const os = require('os');

// Detect platform
const isWindows = os.platform() === 'win32';
const pythonCmd = isWindows ? 'python' : 'python3';

// Determine Python path (try venv first, fallback to system Python)
const venvPython = isWindows 
  ? path.join(__dirname, '.venv', 'Scripts', 'python.exe')
  : path.join(__dirname, '.venv', 'bin', 'python');

const fs = require('fs');
const pythonExecutable = fs.existsSync(venvPython) ? venvPython : pythonCmd;

// Determine yarn command (Windows needs .cmd extension)
const yarnCmd = isWindows ? 'yarn.cmd' : 'yarn';

module.exports = {
  apps: [
    {
      name: 'rag-backend',
      script: pythonExecutable,
      args: '-m uvicorn server:app --host 0.0.0.0 --port 8001',
      cwd: path.join(__dirname, 'backend'),
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        PYTHONUNBUFFERED: '1',
        MONGO_URL: 'mongodb://localhost:27017',
        DB_NAME: 'rag_platform',
        CORS_ORIGINS: '*'
      },
      error_file: path.join(__dirname, 'logs', 'backend-error.log'),
      out_file: path.join(__dirname, 'logs', 'backend-out.log'),
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true
    },
    {
      name: 'rag-frontend',
      script: yarnCmd,
      args: 'start',
      cwd: path.join(__dirname, 'frontend'),
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      env: {
        PORT: '3000',
        BROWSER: 'none',
        REACT_APP_BACKEND_URL: 'http://localhost:8001'
      },
      error_file: path.join(__dirname, 'logs', 'frontend-error.log'),
      out_file: path.join(__dirname, 'logs', 'frontend-out.log'),
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true
    }
  ]
};
