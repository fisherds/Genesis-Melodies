#!/bin/bash
# Setup script for virtual environment

cd "$(dirname "$0")/../.."

echo "🔧 Setting up virtual environment..."

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies (this may take a few minutes)..."
pip install -r functions/requirements.txt

# Install functions-framework for testing
echo "Installing functions-framework for local testing..."
pip install functions-framework

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the venv in the future, run:"
echo "  source .venv/bin/activate"
echo ""
echo "Then test with:"
echo "  cd functions"
echo "  functions-framework --target=search --port=8080"

