#!/bin/bash
# Restart NeuralStark services

echo "Restarting NeuralStark..."

if command -v pm2 &> /dev/null; then
    pm2 restart ecosystem.config.js
    echo "✓ Services restarted"
    echo ""
    echo "View logs with: pm2 logs"
else
    echo "Error: pm2 is not installed!"
    exit 1
fi