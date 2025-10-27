#!/bin/bash
# Start NeuralStark services with pm2 (cross-platform alternative to Supervisor)

echo "Starting NeuralStark with pm2..."

# Check if pm2 is installed
if ! command -v pm2 &> /dev/null; then
    echo "Error: pm2 is not installed!"
    echo "Install with: npm install -g pm2"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start services
pm2 start ecosystem.config.js

# Save pm2 configuration
pm2 save

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              NeuralStark Started! 🚀                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Services:"
echo "- Backend:  http://localhost:8001"
echo "- Frontend: http://localhost:3000"
echo ""
echo "Useful commands:"
echo "- View status: pm2 status"
echo "- View logs:   pm2 logs"
echo "- Stop all:    ./pm2-stop.sh"
echo "- Restart:     ./pm2-restart.sh"
echo ""