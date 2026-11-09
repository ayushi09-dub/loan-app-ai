#!/bin/bash

# Intelligent Loan Approval System - Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Intelligent Loan Approval System${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}Warning: .env file not found!${NC}"
    echo -e "${BLUE}Please create .env with ANTHROPIC_API_KEY${NC}"
    echo ""
fi

# Start services in background
echo -e "${BLUE}Starting services...${NC}"
echo ""

# Start FastAPI
echo -e "${GREEN}Starting FastAPI Backend (Port 8000)...${NC}"
python app/api/main.py > logs/api.log 2>&1 &
API_PID=$!
echo -e "${GREEN}✓ FastAPI PID: $API_PID${NC}"

# Wait for API to start
sleep 2

# Start Streamlit
echo -e "${GREEN}Starting Streamlit UI (Port 8501)...${NC}"
streamlit run app/ui/streamlit_app.py --server.port 8501 --logger.level=warning > logs/streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo -e "${GREEN}✓ Streamlit PID: $STREAMLIT_PID${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Services started successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📊 API Backend: http://localhost:8000${NC}"
echo -e "${BLUE}   - API Docs: http://localhost:8000/docs${NC}"
echo -e "${BLUE}   - Health: http://localhost:8000/health${NC}"
echo ""
echo -e "${BLUE}🏦 Streamlit UI: http://localhost:8501${NC}"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo -e "  - API: logs/api.log${NC}"
echo -e "  - Streamlit: logs/streamlit.log${NC}"
echo ""
echo -e "${BLUE}To stop services:${NC}"
echo -e "  kill $API_PID $STREAMLIT_PID${NC}"
echo ""

# Keep script running
wait
