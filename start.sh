#!/bin/bash

# Intelligent Loan Approval System - Startup Script
# Launches all system components: MCP Servers, FastAPI Backend, and Streamlit UI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Intelligent Loan Approval System${NC}"
echo -e "${BLUE}Multi-Agent Agentic AI Architecture${NC}"
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

# Create logs directory if not exists
mkdir -p logs

# Start services in background
echo -e "${BLUE}Starting services...${NC}"
echo ""

# ============================================
# Phase 1: Start MCP Servers (Infrastructure)
# ============================================
echo -e "${YELLOW}Phase 1: Starting MCP Servers${NC}"

echo -e "${GREEN}Starting ApplicantDB MCP Server (Port 5000)...${NC}"
python app/agents_mcp/applicant_profile/mcp_server.py > logs/mcp_applicant.log 2>&1 &
MCP_APPLICANT_PID=$!
echo -e "${GREEN}✓ ApplicantDB MCP PID: $MCP_APPLICANT_PID${NC}"

echo -e "${GREEN}Starting RiskRulesDB MCP Server (Port 5001)...${NC}"
python app/agents_mcp/financial_risk/mcp_server.py > logs/mcp_financial_risk.log 2>&1 &
MCP_RISK_PID=$!
echo -e "${GREEN}✓ RiskRulesDB MCP PID: $MCP_RISK_PID${NC}"

echo -e "${GREEN}Starting DecisionSynthesis MCP Server (Port 5002)...${NC}"
python app/agents_mcp/loan_decision/mcp_server.py > logs/mcp_decision.log 2>&1 &
MCP_DECISION_PID=$!
echo -e "${GREEN}✓ DecisionSynthesis MCP PID: $MCP_DECISION_PID${NC}"

echo -e "${GREEN}Starting NotificationSystem MCP Server (Port 5003)...${NC}"
python app/agents_mcp/compliance_action/mcp_server.py > logs/mcp_compliance.log 2>&1 &
MCP_COMPLIANCE_PID=$!
echo -e "${GREEN}✓ NotificationSystem MCP PID: $MCP_COMPLIANCE_PID${NC}"

# Wait for MCP servers to initialize
sleep 3

# ============================================
# Phase 2: Start Orchestration & API Layer
# ============================================
echo -e "${YELLOW}Phase 2: Starting FastAPI Backend${NC}"

echo -e "${GREEN}Starting FastAPI Orchestration Service (Port 8000)...${NC}"
python app/api/main.py > logs/api.log 2>&1 &
API_PID=$!
echo -e "${GREEN}✓ FastAPI PID: $API_PID${NC}"

# Wait for API to start
sleep 2

# ============================================
# Phase 3: Start Presentation Layer
# ============================================
echo -e "${YELLOW}Phase 3: Starting Streamlit UI${NC}"

echo -e "${GREEN}Starting Streamlit Chatbot (Port 8501)...${NC}"
streamlit run app/ui/streamlit_app.py --server.port 8501 --logger.level=warning > logs/streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo -e "${GREEN}✓ Streamlit PID: $STREAMLIT_PID${NC}"

# ============================================
# Startup Complete
# ============================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All services started successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📊 MCP Servers (Microservices Layer):${NC}"
echo -e "  - ApplicantDB: localhost:5000${NC}"
echo -e "  - RiskRulesDB: localhost:5001${NC}"
echo -e "  - DecisionSynthesis: localhost:5002${NC}"
echo -e "  - NotificationSystem: localhost:5003${NC}"
echo ""
echo -e "${BLUE}🔄 FastAPI Backend (Orchestration):${NC}"
echo -e "  - API: http://localhost:8000${NC}"
echo -e "  - API Docs: http://localhost:8000/docs${NC}"
echo -e "  - Health: http://localhost:8000/health${NC}"
echo ""
echo -e "${BLUE}🏦 Streamlit UI (Presentation Layer):${NC}"
echo -e "  - UI: http://localhost:8501${NC}"
echo ""
echo -e "${BLUE}📝 Logs:${NC}"
echo -e "  - MCP Servers: logs/mcp_*.log${NC}"
echo -e "  - API: logs/api.log${NC}"
echo -e "  - Streamlit: logs/streamlit.log${NC}"
echo ""
echo -e "${BLUE}To monitor services in real-time:${NC}"
echo -e "  tail -f logs/*.log${NC}"
echo ""
echo -e "${BLUE}To stop all services:${NC}"
echo -e "  kill $MCP_APPLICANT_PID $MCP_RISK_PID $MCP_DECISION_PID $MCP_COMPLIANCE_PID $API_PID $STREAMLIT_PID${NC}"
echo ""

# Save PIDs to file for easy cleanup
cat > .pids << EOF
MCP_APPLICANT_PID=$MCP_APPLICANT_PID
MCP_RISK_PID=$MCP_RISK_PID
MCP_DECISION_PID=$MCP_DECISION_PID
MCP_COMPLIANCE_PID=$MCP_COMPLIANCE_PID
API_PID=$API_PID
STREAMLIT_PID=$STREAMLIT_PID
EOF

echo -e "${YELLOW}PIDs saved to .pids file${NC}"
echo ""

# Keep script running
wait
