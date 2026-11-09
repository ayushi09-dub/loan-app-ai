# Plan: Agentic AI Intelligent Loan Approval System

## Context

The goal is to build a multi-agent AI system that automates loan application analysis using an agentic architecture. The system should classify loan applications as **Approved**, **Rejected**, or **Requires Manual Review** in an explainable, auditable way. This is motivated by the need to replace slow, inconsistent manual/rule-based processes in banking loan approvals.

---

## Architecture Overview

```
User (Streamlit UI)
       |
       v
FastAPI Microservice  ←── Input validation, REST layer
       |
       v
LangGraph Orchestrator  ←── Coordinates agent workflows, manages state
       |
  ┌────┴────────────────────────────┐
  v                                 v
MCP Servers (FastMCP)          LLM (Claude Sonnet 4.6)
  |                                 ^
  ├── ApplicantDB MCP               |
  ├── RiskRulesDB MCP         Synthesizes agent outputs
  ├── DecisionSynthesis MCP        into final decision
  └── NotificationSystem MCP
  |
  ├── Applicant Profile Agent
  ├── Financial Risk Analysis Agent
  ├── Loan Decision Agent
  └── Compliance & Action Orchestrator Agent
```

---

## Directory Structure

```
loan-app-ai/
├── README.md
├── PLAN.md                       # This plan (copy here post-build)
├── requirements.txt
├── .env                          # API keys (ANTHROPIC_API_KEY)
├── app/
│   ├── ui/
│   │   └── streamlit_app.py      # Chatbot UI
│   ├── api/
│   │   └── main.py               # FastAPI microservice
│   ├── orchestrator/
│   │   └── langgraph_engine.py   # LangGraph orchestration
│   └── agents_mcp/               # Agents and their MCP servers co-located
│       ├── applicant_profile/
│       │   ├── agent.py          # Applicant Profile Agent
│       │   └── mcp_server.py     # ApplicantDB MCP server
│       ├── financial_risk/
│       │   ├── agent.py          # Financial Risk Agent
│       │   └── mcp_server.py     # RiskRulesDB MCP server
│       ├── loan_decision/
│       │   ├── agent.py          # Loan Decision Agent
│       │   └── mcp_server.py     # DecisionSynthesis MCP server
│       └── compliance_action/
│           ├── agent.py          # Compliance & Action Orchestrator Agent
│           └── mcp_server.py     # NotificationSystem MCP server
└── tests/
    └── test_loan_flow.py
```

---

## Implementation Plan

### Step 1: Project Setup & Dependencies

**File:** `requirements.txt`

```
anthropic
langchain
langgraph
langchain-anthropic
fastmcp
fastapi
uvicorn
streamlit
httpx
python-dotenv
pydantic
```

Create `.env` with `ANTHROPIC_API_KEY`.

---

### Step 2: Agents & MCP Servers (Co-located Modules)

Each module contains both an **Agent** and its corresponding **MCP Server**, keeping related functionality together.

#### Module: `app/agents_mcp/applicant_profile/`

**MCP Server** (`mcp_server.py` — ApplicantDB):
- `get_applicant_profile(applicant_id)` → returns age, income, employment type
- `get_credit_history(applicant_id)` → returns credit score, history summary
- `check_application_completeness(data)` → validates all fields present

**Agent** (`agent.py` — Applicant Profile Agent):
- Uses Anthropic Claude Sonnet 4.6 via Anthropic Agent SDK
- Connects to ApplicantDB MCP server
- Outputs: `income_stability_score`, `employment_risk`, `credit_history_summary`, `completeness_flags`

#### Module: `app/agents_mcp/financial_risk/`

**MCP Server** (`mcp_server.py` — RiskRulesDB):
- `calculate_dti(income, liabilities, loan_amount)` → debt-to-income ratio
- `evaluate_credit_risk(credit_score)` → risk level (Low/Medium/High)
- `detect_anomalies(application_data)` → flags unusual patterns

**Agent** (`agent.py` — Financial Risk Agent):
- Uses Anthropic Claude Sonnet 4.6 via Anthropic Agent SDK
- Connects to RiskRulesDB MCP server
- Outputs: `dti_ratio`, `credit_score_risk`, `loan_amount_risk`, `anomaly_flags`, `reasoning`

#### Module: `app/agents_mcp/loan_decision/`

**MCP Server** (`mcp_server.py` — DecisionSynthesis):
- `synthesize_decision(profile_output, risk_output)` → classification + risk score + confidence
- `generate_explanation(decision_data)` → human-readable explanation

**Agent** (`agent.py` — Loan Decision Agent):
- Uses Anthropic Claude Sonnet 4.6 via Anthropic Agent SDK
- Connects to DecisionSynthesis MCP server
- Outputs: `classification` (Approve/Reject/Review), `risk_score`, `confidence_level`, `key_factors`, `explanation`

#### Module: `app/agents_mcp/compliance_action/`

**MCP Server** (`mcp_server.py` — NotificationSystem):
- `send_notification(applicant_id, decision, explanation)` → logs + returns case ID
- `record_audit_trail(case_id, all_agent_outputs)` → stores for compliance

**Agent** (`agent.py` — Compliance & Action Orchestrator Agent):
- Uses Anthropic Claude Sonnet 4.6 via Anthropic Agent SDK
- Connects to NotificationSystem MCP server
- Outputs: `action_taken`, `notification_sent`, `case_id`, `timestamp`, `summary`

**Architecture benefit:** Each agent-MCP module is self-contained and can be developed, tested, and deployed independently.

Agent pattern (using Anthropic SDK with MCP):
```python
import anthropic

client = anthropic.Anthropic()

# Each agent uses client.beta.messages.create with tools from its co-located MCP server
# Tools are defined as MCP tool schemas
```

---

### Step 3: LangGraph Orchestration Engine

**File:** `app/orchestrator/langgraph_engine.py`

Defines the state graph:

```
START
  └─► applicant_profile_node        (calls app.agents_mcp.applicant_profile.agent)
           └─► financial_risk_node  (calls app.agents_mcp.financial_risk.agent)
                    └─► loan_decision_node  (calls app.agents_mcp.loan_decision.agent)
                              └─► compliance_node  (calls app.agents_mcp.compliance_action.agent)
                                        └─► END
```

**State schema (TypedDict):**
```python
class LoanState(TypedDict):
    application_data: dict
    profile_output: dict
    risk_output: dict
    decision_output: dict
    compliance_output: dict
    final_result: dict
```

Each node imports and calls the corresponding agent from its module, updates state, and passes to the next node. Conditional edges can route to `compliance_node` directly if a hard rejection is detected early.

---

### Step 4: FastAPI Microservice

**File:** `app/api/main.py`

```
POST /loan/apply     → Accepts loan application JSON → triggers orchestrator → returns decision
GET  /loan/status/{case_id}  → Returns case status
GET  /health         → Health check
```

Input model (Pydantic):
```python
class LoanApplication(BaseModel):
    applicant_id: str
    age: int
    income: float
    employment_type: str
    credit_score: int
    loan_amount: float
    tenure_months: int
    existing_liabilities: float
    location: str
    timestamp: str
```

The endpoint instantiates the LangGraph engine, runs it with the application data, and returns the `final_result`.

---

### Step 5: Streamlit Chatbot UI

**File:** `app/ui/streamlit_app.py`

- Form-based input for all loan application fields
- Chatbot-style output panel showing:
  - Agent-by-agent analysis steps (expandable)
  - Final decision badge (Approved / Rejected / Manual Review)
  - Risk score, confidence, explanation
  - Case ID and audit trail link
- Uses `httpx` to call the FastAPI backend

---

### Step 6: Running the System

**Architecture Pattern: Persistent Background Services**

MCP servers run as **independent, always-available microservices** (not managed by orchestrator). This implements the "loosely coupled microservices architecture" requirement from the problem statement.

Start all components in separate terminals:

```bash
# Terminal 1: Start MCP servers (persistent background microservices)
# These run independently and serve all agents
python app/agents_mcp/applicant_profile/mcp_server.py       # Port 5000
python app/agents_mcp/financial_risk/mcp_server.py          # Port 5001
python app/agents_mcp/loan_decision/mcp_server.py           # Port 5002
python app/agents_mcp/compliance_action/mcp_server.py       # Port 5003

# Terminal 2: Start FastAPI microservice (orchestration & API layer)
uvicorn app.api.main:app --reload --port 8000

# Terminal 3: Start Streamlit chatbot UI
streamlit run app/ui/streamlit_app.py
```

**Justification:**
- ✅ True microservices: each server is independent
- ✅ Loosely coupled: servers don't depend on orchestrator
- ✅ Scalable: servers can run on different machines
- ✅ Production-ready: standard microservices pattern
- ✅ Fault isolation: server crash doesn't crash orchestrator

**Deployment flexibility:**
- Servers can be containerized and deployed to Kubernetes/Docker
- Agents can connect via HTTP or stdio
- Easy to add new agents without restarting existing servers

---

## Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| LLM | Claude Sonnet 4.6 | Specified in requirements; strong reasoning |
| Agent SDK | Anthropic SDK (`client.beta.messages`) | Native tool use with MCP |
| MCP Framework | FastMCP | Lightweight, Python-native MCP server |
| Orchestration | LangGraph | State machine model fits sequential agent pipeline |
| API layer | FastAPI | Fast, typed, async-ready |
| UI | Streamlit | Rapid prototyping, chatbot-friendly |
| Agent communication | MCP servers (HTTP/stdio) | Standardized, loosely coupled |

---

## Verification

1. **Unit test each MCP server** — call tools directly and verify outputs
2. **Unit test each agent** — pass mock application data, verify structured output
3. **Integration test** — POST to `/loan/apply` with a sample application; confirm full pipeline runs and returns `classification`
4. **UI test** — fill Streamlit form, submit, verify decision displayed correctly
5. **Edge cases** — missing fields (completeness check), very low credit score (hard reject), borderline DTI (manual review)

Test file: `tests/test_loan_flow.py` using `pytest` and `httpx.AsyncClient`.

---

## Files to Create (in order)

1. `requirements.txt`
2. `.env` (template)
3. `app/agents_mcp/applicant_profile/mcp_server.py`
4. `app/agents_mcp/applicant_profile/agent.py`
5. `app/agents_mcp/financial_risk/mcp_server.py`
6. `app/agents_mcp/financial_risk/agent.py`
7. `app/agents_mcp/loan_decision/mcp_server.py`
8. `app/agents_mcp/loan_decision/agent.py`
9. `app/agents_mcp/compliance_action/mcp_server.py`
10. `app/agents_mcp/compliance_action/agent.py`
11. `app/orchestrator/langgraph_engine.py`
12. `app/api/main.py`
13. `app/ui/streamlit_app.py`
14. `tests/test_loan_flow.py`
15. `PLAN.md` (copy of this plan)
16. `start.sh`
