#!/bin/bash
# Setup script for LED AI Copilot
echo "=== LED AI Copilot Setup ==="

# Backend setup
echo "Setting up backend..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Frontend setup
echo "Setting up frontend..."
cd frontend
npm install
cd ..

# Create directories
mkdir -p uploads exports chroma_data

# Copy env file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file. Please edit with your API keys."
fi

echo "=== Setup complete ==="
echo "Run 'docker-compose up' or start services manually."
