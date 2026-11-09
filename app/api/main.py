from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import sys
import os
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from orchestrator.langgraph_engine import run_loan_application

app = FastAPI(
    title="Intelligent Loan Approval System API",
    description="Multi-agent AI system for loan application analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

case_storage = {}


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
    timestamp: Optional[str] = None


class LoanDecision(BaseModel):
    case_id: str
    classification: str
    risk_score: float
    confidence_level: float
    explanation: str
    profile_output: dict
    risk_output: dict
    decision_output: dict
    compliance_output: dict


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Loan Approval API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/loan/apply", response_model=dict)
async def submit_loan_application(application: LoanApplication):
    """
    Submit a loan application for processing.

    Triggers the multi-agent orchestration workflow:
    1. Applicant Profile Analysis
    2. Financial Risk Assessment
    3. Loan Decision Synthesis
    4. Compliance & Action Orchestration

    Returns the final decision with detailed analysis.
    """
    try:
        application_data = application.model_dump()
        if not application_data.get("timestamp"):
            application_data["timestamp"] = datetime.now().isoformat()

        result = run_loan_application(application_data)

        case_id = result.get("case_id", f"CASE-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        case_storage[case_id] = result

        return {
            "success": True,
            "case_id": case_id,
            "classification": result.get("classification"),
            "risk_score": result.get("risk_score"),
            "confidence_level": result.get("confidence_level"),
            "explanation": result.get("explanation"),
            "key_factors": result.get("decision_output", {}).get("key_factors", []),
            "next_steps": result.get("decision_output", {}).get("next_steps", []),
            "timestamp": result.get("timestamp"),
            "full_analysis": result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Application processing failed: {str(e)}")


@app.get("/loan/status/{case_id}")
async def get_loan_status(case_id: str):
    """
    Get the status of a previously submitted loan application.

    Returns:
    - Classification (APPROVED/REJECTED/MANUAL_REVIEW)
    - Risk score and confidence level
    - Complete analysis from all agents
    - Audit trail information
    """
    if case_id not in case_storage:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    case = case_storage[case_id]

    return {
        "case_id": case_id,
        "classification": case.get("classification"),
        "risk_score": case.get("risk_score"),
        "confidence_level": case.get("confidence_level"),
        "status": "PROCESSED",
        "timestamp": case.get("timestamp"),
        "analysis": {
            "profile": case.get("profile_output"),
            "risk": case.get("risk_output"),
            "decision": case.get("decision_output"),
            "compliance": case.get("compliance_output"),
        },
    }


@app.get("/loan/cases")
async def list_cases():
    """List all processed loan cases"""
    cases = []
    for case_id, case_data in case_storage.items():
        cases.append(
            {
                "case_id": case_id,
                "applicant_id": case_data.get("applicant_data", {}).get("applicant_id"),
                "classification": case_data.get("classification"),
                "risk_score": case_data.get("risk_score"),
                "timestamp": case_data.get("timestamp"),
            }
        )

    return {"total_cases": len(cases), "cases": cases}


@app.post("/loan/test")
async def test_application():
    """Test endpoint with sample data"""
    test_data = LoanApplication(
        applicant_id="TEST-001",
        age=35,
        income=75000,
        employment_type="Salaried",
        credit_score=750,
        loan_amount=250000,
        tenure_months=60,
        existing_liabilities=50000,
        location="New York",
    )

    return await submit_loan_application(test_data)


@app.get("/")
async def root():
    """API root with documentation"""
    return {
        "service": "Intelligent Loan Approval System",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "apply": {
                "method": "POST",
                "path": "/loan/apply",
                "description": "Submit loan application",
            },
            "status": {
                "method": "GET",
                "path": "/loan/status/{case_id}",
                "description": "Get application status",
            },
            "cases": {
                "method": "GET",
                "path": "/loan/cases",
                "description": "List all cases",
            },
            "test": {
                "method": "POST",
                "path": "/loan/test",
                "description": "Test with sample data",
            },
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
