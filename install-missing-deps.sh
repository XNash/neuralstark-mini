#!/bin/bash
# Quick script to install missing dependencies after setup

echo "=========================================="
echo "Installing Missing Dependencies"
echo "=========================================="
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "❌ Virtual environment not found at .venv/"
    echo "Please run ./run.sh first to create it"
    exit 1
fi

echo ""
echo "Installing required packages..."
echo "This will take a few minutes..."
echo ""

# Install all dependencies from requirements.txt
pip install -r backend/requirements.txt 2>&1 | grep -E "(Installing|Requirement already satisfied|Successfully installed|ERROR)" | tail -20

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Now restart the backend:"
echo "  sudo supervisorctl restart backend"
echo ""
echo "Check if it's running:"
echo "  curl http://localhost:8001/api/"
echo ""
