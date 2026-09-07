#!/bin/bash

# Complete startup script for Bunny Buddy backend

echo "═════════════════════════════════════════════════"
echo "  BUNNY BUDDY - Starting All Services"
echo "═════════════════════════════════════════════════"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Kill any existing processes on ports
echo -e "\n${YELLOW}[1/4] Cleaning up old processes...${NC}"
lsof -i :8000 | grep -v COMMAND | awk '{print $2}' | xargs kill -9 2>/dev/null
lsof -i :3000 | grep -v COMMAND | awk '{print $2}' | xargs kill -9 2>/dev/null
sleep 1

# Start Chroma
echo -e "\n${YELLOW}[2/4] Starting Chroma Vector Store (port 8000)...${NC}"
chroma run --path ./chroma_data --port 8000 &
CHROMA_PID=$!
sleep 3
if curl -s http://localhost:8000/api/v1/ > /dev/null 2>&1; then
  echo -e "${GREEN}✅ Chroma ready${NC}"
else
  echo -e "${YELLOW}⏳ Chroma starting...${NC}"
fi

# Start Ollama
echo -e "\n${YELLOW}[3/4] Starting Ollama (port 11434)...${NC}"
ollama serve &
OLLAMA_PID=$!
sleep 5
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
  echo -e "${GREEN}✅ Ollama ready${NC}"
else
  echo -e "${YELLOW}⏳ Ollama starting...${NC}"
fi

# Start Backend
echo -e "\n${YELLOW}[4/4] Starting Node.js Backend (port 3000)...${NC}"
cd "$(dirname "$0")" || exit
npm start &
BACKEND_PID=$!
sleep 3

# Health check
echo -e "\n${GREEN}═════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  All services started!${NC}"
echo -e "${GREEN}═════════════════════════════════════════════════${NC}"

echo -e "\n${YELLOW}Services running:${NC}"
echo -e "  ✅ Chroma:  http://localhost:8000 (PID: $CHROMA_PID)"
echo -e "  ✅ Ollama:  http://localhost:11434 (PID: $OLLAMA_PID)"
echo -e "  ✅ Backend: http://localhost:3000 (PID: $BACKEND_PID)"

echo -e "\n${YELLOW}Open in browser:${NC}"
echo -e "  🌐 http://localhost:3000/avatar.html"
echo -e "  🌐 http://localhost:3000/ (test page)"

echo -e "\n${YELLOW}To stop all services, press Ctrl+C${NC}\n"

# Keep script running
wait
