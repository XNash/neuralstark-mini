/**
 * Windows-compatible start script
 * Usage: node start-windows.js
 */

const { spawn } = require('child_process');
const path = require('path');

// Set NODE_OPTIONS to suppress deprecation warnings
process.env.NODE_OPTIONS = '--no-deprecation';

// Path to craco
const cracoBin = process.platform === 'win32' 
  ? path.join(__dirname, 'node_modules', '.bin', 'craco.cmd')
  : path.join(__dirname, 'node_modules', '.bin', 'craco');

console.log('Starting development server...');

// Spawn craco process
const child = spawn(cracoBin, ['start'], {
  stdio: 'inherit',
  shell: true,
  env: { ...process.env }
});

child.on('error', (error) => {
  console.error('Failed to start:', error);
  process.exit(1);
});

child.on('exit', (code) => {
  process.exit(code);
});
