#!/bin/bash
# Setup script for GENIE project

echo "Setting up GENIE project..."

# Check if Python 3.11+ is available
python3 --version

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
python3 -m pip install --upgrade pip

# Install Poetry
pip install poetry

# Install dependencies
poetry install

# Create necessary directories
mkdir -p data/{search_library,configs,uploads}
mkdir -p logs

# Copy .env.example to .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example - Please add your API keys"
fi

echo "Setup complete!"
echo "To activate the environment, run: source venv/bin/activate"
echo "To start the server, run: uvicorn spec.main:app --reload"
