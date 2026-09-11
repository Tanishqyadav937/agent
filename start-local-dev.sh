#!/bin/bash

# Quick Local Development Setup Script
# Starts Chroma (SQLite) + Your Voice Assistant Backend
# Usage: chmod +x start-local-dev.sh && ./start-local-dev.sh

set -e  # Exit on error

echo "════════════════════════════════════════════════════════════════"
echo "  Local Voice Assistant Development Setup"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed and running
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker not found. Please install Docker first.${NC}"
    echo "Visit: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker ps &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker daemon not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠️  Node.js not found. Please install Node.js first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Node.js is installed${NC}"
echo ""

# Check if Ollama is running (optional, for local LLM)
echo -e "${BLUE}Checking Ollama (optional for local LLM)...${NC}"
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
else
    echo -e "${YELLOW}ℹ️  Ollama not running (optional)${NC}"
    echo "   If you want to use local models, start Ollama: ollama serve"
fi
echo ""

# Start Chroma server
echo -e "${BLUE}Starting Chroma Server (SQLite)...${NC}"

# Check if Chroma container already running
if docker ps | grep -q chroma-local; then
    echo -e "${GREEN}✓ Chroma is already running${NC}"
else
    # Check if image exists
    if ! docker images | grep -q chromadb/chroma; then
        echo "  Pulling Chroma Docker image (this may take a moment)..."
    fi
    
    # Create volume if needed
    if ! docker volume ls | grep -q chroma-data; then
        echo "  Creating chroma-data volume..."
        docker volume create chroma-data
    fi
    
    # Start Chroma
    echo "  Starting Chroma container..."
    docker run -d \
        --name chroma-local \
        -p 8000:8000 \
        -v chroma-data:/chroma/chroma-data \
        chromadb/chroma
    
    # Wait for Chroma to be ready
    echo "  Waiting for Chroma to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/v1/heartbeat &> /dev/null; then
            echo -e "${GREEN}✓ Chroma server started successfully${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${YELLOW}⚠️  Chroma took too long to start${NC}"
        fi
        sleep 1
    done
fi
echo ""

# Check .env file
echo -e "${BLUE}Checking .env configuration...${NC}"

if [ ! -f .env ]; then
    echo "  Creating .env from template..."
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env${NC}"
    echo "  Note: Update .env with your API keys if needed"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi
echo ""

# Verify Chroma connectivity
echo -e "${BLUE}Verifying Chroma connectivity...${NC}"

if curl -s http://localhost:8000/api/v1/heartbeat | grep -q "OK"; then
    echo -e "${GREEN}✓ Chroma is reachable at http://localhost:8000${NC}"
else
    echo -e "${YELLOW}⚠️  Could not reach Chroma. It may still be starting...${NC}"
fi
echo ""

echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}Setup Complete!${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo ""
echo "1. Start your backend in a new terminal:"
echo -e "   ${BLUE}npm start${NC}"
echo ""
echo "2. Test the API:"
echo -e "   ${BLUE}curl http://localhost:3000/health | jq .${NC}"
echo ""
echo "3. Test conversation with memory:"
echo -e "   ${BLUE}curl -X POST http://localhost:3000/converse-text \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"sessionId\": \"test\", \"user_input\": \"Hello\"}'${NC}"
echo ""
echo "Services running:"
echo "  • Chroma Server:       http://localhost:8000"
echo "  • Voice Assistant:     http://localhost:3000 (after npm start)"
echo "  • Ollama (if running): http://localhost:11434"
echo ""
echo "To view logs:"
echo -e "   ${BLUE}docker-compose logs -f chroma${NC}"
echo ""
echo "To stop services:"
echo -e "   ${BLUE}docker-compose down${NC}"
echo ""
