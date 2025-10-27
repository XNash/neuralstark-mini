#!/bin/bash
# Stop NeuralStark services

echo "Stopping NeuralStark..."

if command -v pm2 &> /dev/null; then
    pm2 stop ecosystem.config.js
    pm2 save
    echo "✓ Services stopped"
else
    echo "Error: pm2 is not installed!"
    exit 1
fi