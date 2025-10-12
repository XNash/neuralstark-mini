#!/bin/bash
# Post-Clone Setup Script
# Run this after cloning the repository to set up the environment

set -e

echo "============================================"
echo "RAG Platform - Post-Clone Setup"
echo "============================================"
echo ""

# Check if we're in the right directory
if [ ! -f "run.sh" ]; then
    echo "❌ Error: run.sh not found"
    echo "Please run this script from the repository root"
    exit 1
fi

echo "✓ Repository structure verified"
echo ""

# Step 1: Create environment files if they don't exist
echo "Step 1: Setting up environment files..."
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "  ✓ Created backend/.env from .env.example"
else
    echo "  ✓ backend/.env already exists"
fi

if [ ! -f "frontend/.env" ]; then
    cp frontend/.env.example frontend/.env
    echo "  ✓ Created frontend/.env from .env.example"
else
    echo "  ✓ frontend/.env already exists"
fi

echo ""

# Step 2: Make scripts executable
echo "Step 2: Making scripts executable..."
chmod +x run.sh
chmod +x verify-configuration.sh
chmod +x test-permanent-config.sh
chmod +x verify-setup.sh
chmod +x diagnose.sh
echo "  ✓ All scripts are now executable"
echo ""

# Step 3: Display next steps
echo "============================================"
echo "✅ Post-Clone Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Run the universal setup script:"
echo "   ./run.sh"
echo ""
echo "2. This will:"
echo "   - Install all system dependencies"
echo "   - Create virtual environment at .venv/"
echo "   - Set up cache directories at .cache/"
echo "   - Install backend and frontend dependencies"
echo "   - Configure and start all services"
echo ""
echo "3. After setup completes, verify with:"
echo "   ./verify-configuration.sh"
echo ""
echo "4. Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8001/api/"
echo ""
echo "5. Configure your API key:"
echo "   - Open http://localhost:3000"
echo "   - Go to Settings page"
echo "   - Add your Gemini API key"
echo "   - Get key from: https://aistudio.google.com/app/apikey"
echo ""
echo "For detailed instructions, see:"
echo "  - FIRST_TIME_SETUP.md"
echo "  - README.md"
echo ""
