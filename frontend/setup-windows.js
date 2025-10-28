/**
 * Windows Setup Script for NeuralStark Frontend
 * This script runs after yarn install to ensure Windows compatibility
 */

const fs = require('fs');
const path = require('path');

console.log('🪟 Setting up NeuralStark for Windows compatibility...');

// Check if running on Windows
const isWindows = process.platform === 'win32';

if (isWindows) {
  console.log('✓ Windows platform detected');
  
  // Check for craco.cmd (Windows command file)
  const cracoCmdPath = path.join(__dirname, 'node_modules', '.bin', 'craco.cmd');
  if (fs.existsSync(cracoCmdPath)) {
    console.log('✓ craco.cmd found - Windows support enabled');
  } else {
    console.log('⚠ Warning: craco.cmd not found in node_modules/.bin/');
  }
} else {
  console.log('✓ Unix-like platform detected');
}

// Create a simple start script for Windows
const startScriptPath = path.join(__dirname, 'start-windows.js');
const startScriptContent = `/**
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
`;

fs.writeFileSync(startScriptPath, startScriptContent);
console.log('✓ Created start-windows.js for direct Windows usage');

console.log('\n📝 Usage instructions:');
console.log('  Windows (PowerShell/CMD): yarn start:win');
console.log('  Windows (alternative):     node start-windows.js');
console.log('  Unix/Linux/Mac:           yarn start:unix');
console.log('  Cross-platform:           yarn start (requires cross-env)');
console.log('\n✨ Windows setup complete!\n');
