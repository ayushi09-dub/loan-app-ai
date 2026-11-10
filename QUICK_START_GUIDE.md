# Quick Start Guide - Updated

This guide covers running the updated Intelligent Loan Approval System with all recent fixes applied.

---

## Prerequisites

- Python 3.8+
- `.env` file with `ANTHROPIC_API_KEY` configured
- 4 available ports: 5000-5003 (MCP servers), 8000 (API), 8501 (Streamlit)

---

## Starting the System

### Option 1: Automated (Recommended)

```bash
# Make script executable
chmod +x start.sh

# Run the startup script
./start.sh
```

This will:
1. ✅ Create/activate virtual environment
2. ✅ Install dependencies
3. ✅ Start 4 MCP servers (Phase 1)
4. ✅ Start FastAPI backend (Phase 2)  
5. ✅ Start Streamlit UI (Phase 3)
6. ✅ Save PIDs to `.pids` for easy cleanup

**Output will show:**
```
Phase 1: Starting MCP Servers
✓ ApplicantDB MCP PID: xxxx
✓ RiskRulesDB MCP PID: xxxx
✓ DecisionSynthesis MCP PID: xxxx
✓ NotificationSystem MCP PID: xxxx

Phase 2: Starting FastAPI Backend
✓ FastAPI PID: xxxx

Phase 3: Starting Streamlit UI
✓ Streamlit PID: xxxx
```

### Option 2: Manual (For Debugging)

**Terminal 1 - MCP Servers:**
```bash
source venv/bin/activate
python app/agents_mcp/applicant_profile/mcp_server.py
```

**Terminal 2 - More MCP Servers:**
```bash
source venv/bin/activate
python app/agents_mcp/financial_risk/mcp_server.py
python app/agents_mcp/loan_decision/mcp_server.py
python app/agents_mcp/compliance_action/mcp_server.py
```

**Terminal 3 - API:**
```bash
source venv/bin/activate
uvicorn app.api.main:app --reload --port 8000
```

**Terminal 4 - UI:**
```bash
source venv/bin/activate
streamlit run app/ui/streamlit_app.py
```

---

## Accessing the System

Once running, access via:

| Component | URL | Purpose |
|-----------|-----|---------|
| **Streamlit UI** | http://localhost:8501 | Submit applications |
| **FastAPI Docs** | http://localhost:8000/docs | API documentation |
| **Health Check** | http://localhost:8000/health | System status |
| **MCP Servers** | localhost:5000-5003 | Background microservices |

---

## Using the Application

### Via Streamlit UI (Recommended)

1. Open http://localhost:8501
2. Fill in applicant details:
   - Applicant ID
   - Age
   - Income
   - Employment Type
   - Credit Score
   - Loan Amount
   - Tenure
   - Existing Liabilities
   - Location

3. Click "🚀 Submit Application"

4. View results:
   - Step-by-step agent analysis
   - Risk score and confidence
   - Final decision (Approved/Rejected/Manual Review)
   - Full audit trail

### Via REST API

**Submit Application:**
```bash
curl -X POST http://localhost:8000/loan/apply \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP-001",
    "age": 35,
    "income": 75000,
    "employment_type": "Salaried",
    "credit_score": 750,
    "loan_amount": 250000,
    "tenure_months": 60,
    "existing_liabilities": 50000,
    "location": "New York"
  }'
```

**Check Application Status:**
```bash
curl http://localhost:8000/loan/status/CASE-20261110-ABC123
```

**List All Cases:**
```bash
curl http://localhost:8000/loan/cases
```

---

## Stopping the System

### If Using Automated Script:

```bash
# Stop using saved PIDs
source .pids
kill $MCP_APPLICANT_PID $MCP_RISK_PID $MCP_DECISION_PID $MCP_COMPLIANCE_PID $API_PID $STREAMLIT_PID
```

### If Using Manual Terminals:

```bash
# In each terminal, press Ctrl+C
```

---

## What's New (Recent Fixes)

### ✅ UI Improvements
- Risk score now displays with dynamic color and label
- "Low Risk", "Medium Risk", "High Risk" badges show correctly

### ✅ Enhanced Prompts
- All 4 agents have better guidance for decision-making
- Clearer scoring criteria and reasoning

### ✅ Better Startup
- start.sh now launches full microservices architecture
- MCP servers start first (as per PLAN.md)
- Clear phase-based output and logging

### ✅ Documentation
- Updated to show Haiku model instead of Sonnet
- Clearer technical specifications

---

## Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :8000
lsof -i :5000

# Kill process
kill -9 <PID>
```

### API Connection Error
```
Error: Backend API not available
```
**Solution:** Ensure FastAPI is running on terminal 3:
```bash
uvicorn app.api.main:app --reload --port 8000
```

### Missing API Key
```bash
# Add to .env
ANTHROPIC_API_KEY=your-key-here
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_MODEL=global.anthropic.claude-haiku-4-5-20251001-v1:0
```

### Tests Failing
```bash
# Run tests with virtual environment
source venv/bin/activate
python -m pytest tests/test_loan_flow.py -v
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI (Port 8501)                 │
│              📱 Loan Application Submission                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                    │
│         🔄 Orchestration & REST Endpoints                   │
└────────────────────┬────────────────────────────────────────┘
                     │
     ┌───────────────┼───────────────┐
     ▼               ▼               ▼               ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ MCP 5000 │   │ MCP 5001 │   │ MCP 5002 │   │ MCP 5003 │
│ApplicDB  │   │RiskRules │   │Decision  │   │Notif.    │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
    ▲               ▲               ▲               ▲
    └───────────────┼───────────────┼───────────────┘
                    │
           🤖 Claude Agents 🤖
    (Each agent analyzes its domain)
```

---

## Performance Expectations

- **API Response Time:** 5-15 seconds (depends on Claude API latency)
- **UI Load:** < 1 second
- **MCP Server Startup:** ~ 2 seconds
- **Full System Startup:** ~ 10-15 seconds

---

## Support & Debugging

### View Logs

```bash
# Watch all logs in real-time
tail -f logs/*.log

# Specific service logs
tail -f logs/api.log
tail -f logs/streamlit.log
tail -f logs/mcp_*.log
```

### Check System Health

```bash
# Health endpoint
curl http://localhost:8000/health

# API Documentation
curl http://localhost:8000/

# Test endpoint with sample data
curl -X POST http://localhost:8000/loan/test
```

### Debug Agent Responses

1. Check Streamlit UI for step-by-step analysis
2. View full_analysis in response with expandable sections
3. Check logs for API and agent execution traces

---

## Configuration

Edit `.env` to customize:

```bash
# Claude API Configuration
ANTHROPIC_API_KEY=sk-xxx...
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_MODEL=global.anthropic.claude-haiku-4-5-20251001-v1:0

# Optional: Change model to Sonnet for better quality
# ANTHROPIC_MODEL=claude-opus-5-5-20251105
```

---

## Documentation Files

For more detailed information, see:

- **README.md** - Problem statement and overall system design
- **PLAN.md** - Detailed technical architecture
- **ISSUES_FOUND.md** - Comprehensive issue analysis
- **FIXES_APPLIED.md** - Changes made and next steps
- **CODE_REVIEW_SUMMARY.md** - Executive summary of review
- **BUILD_SUMMARY.md** - Initial build information

---

## Next Steps

1. ✅ Start the system using `./start.sh`
2. ✅ Open Streamlit UI at localhost:8501
3. ✅ Submit a test application
4. ✅ View the results and agent analysis
5. 🔜 Review ISSUES_FOUND.md for planned improvements

---

**Last Updated:** 2026-11-10  
**Status:** Ready for testing and deployment

