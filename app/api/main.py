from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import sys
import os
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from orchestrator.langgraph_engine import run_loan_application
from storage import get_storage

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
        # Validate input data
        if application.income <= 0:
            raise ValueError("Income must be greater than 0")
        if application.credit_score < 300 or application.credit_score > 850:
            raise ValueError("Credit score must be between 300 and 850")
        if application.loan_amount <= 0:
            raise ValueError("Loan amount must be greater than 0")
        if application.age < 18 or application.age > 120:
            raise ValueError("Age must be between 18 and 120")

        application_data = application.model_dump()
        if not application_data.get("timestamp"):
            application_data["timestamp"] = datetime.now().isoformat()

        try:
            result = run_loan_application(application_data)
        except Exception as workflow_error:
            raise HTTPException(
                status_code=500,
                detail=f"Workflow execution failed: {str(workflow_error)}"
            )

        if not result or not isinstance(result, dict):
            raise HTTPException(
                status_code=500,
                detail="Invalid response from orchestrator"
            )

        case_id = result.get("case_id", f"CASE-{datetime.now().strftime('%Y%m%d%H%M%S')}")

        # Store with metadata in memory and persistent storage
        case_data = {
            **result,
            "stored_at": datetime.now().isoformat(),
            "application_id": application.applicant_id,
        }

        case_storage[case_id] = case_data

        # Save to persistent storage
        storage = get_storage()
        storage.save_case(case_id, case_data)

        return {
            "success": True,
            "case_id": case_id,
            "classification": result.get("classification", "UNKNOWN"),
            "risk_score": result.get("risk_score", 0),
            "confidence_level": result.get("confidence_level", 0),
            "explanation": result.get("explanation", "N/A"),
            "key_factors": result.get("decision_output", {}).get("key_factors", []),
            "next_steps": result.get("decision_output", {}).get("next_steps", []),
            "timestamp": result.get("timestamp"),
            "full_analysis": result,
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(ve)}")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error processing application: {error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"Application processing failed: {str(e)}"
        )


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
    if not case_id:
        raise HTTPException(status_code=400, detail="Case ID cannot be empty")

    # Check in-memory storage first
    case = case_storage.get(case_id)

    # If not in memory, check persistent storage
    if not case:
        storage = get_storage()
        case = storage.load_case(case_id)
        if case:
            case_storage[case_id] = case

    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    try:

        return {
            "case_id": case_id,
            "classification": case.get("classification", "UNKNOWN"),
            "risk_score": case.get("risk_score", 0),
            "confidence_level": case.get("confidence_level", 0),
            "status": "PROCESSED",
            "timestamp": case.get("timestamp"),
            "stored_at": case.get("stored_at"),
            "analysis": {
                "profile": case.get("profile_output", {}),
                "risk": case.get("risk_output", {}),
                "decision": case.get("decision_output", {}),
                "compliance": case.get("compliance_output", {}),
            },
            "audit": {
                "case_id": case_id,
                "audit_recorded": case.get("compliance_output", {}).get("audit_recorded", False),
                "timestamp": case.get("timestamp"),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving case status: {str(e)}")


@app.get("/loan/cases")
async def list_cases(limit: int = 50):
    """List all processed loan cases"""
    try:
        storage = get_storage()
        storage_cases = storage.list_cases(limit=limit)

        cases = []
        for case_info in storage_cases:
            cases.append({
                "case_id": case_info.get("case_id"),
                "applicant_id": case_info.get("applicant_id", "N/A"),
                "classification": case_info.get("classification", "UNKNOWN"),
                "timestamp": case_info.get("timestamp"),
                "stored_at": case_info.get("stored_at"),
            })

        return {
            "total_cases": len(cases),
            "limit": limit,
            "cases": cases,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing cases: {str(e)}")


@app.get("/loan/statistics")
async def get_statistics():
    """Get system statistics and analytics"""
    try:
        storage = get_storage()
        stats = storage.get_statistics()

        # Add in-memory stats
        stats["in_memory_cases"] = len(case_storage)

        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")


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
        "description": "Multi-agent AI system for automated loan approval analysis",
        "endpoints": {
            "health": {
                "method": "GET",
                "path": "/health",
                "description": "System health check",
            },
            "apply": {
                "method": "POST",
                "path": "/loan/apply",
                "description": "Submit loan application for processing",
            },
            "status": {
                "method": "GET",
                "path": "/loan/status/{case_id}",
                "description": "Get application status by case ID",
            },
            "cases": {
                "method": "GET",
                "path": "/loan/cases?limit=50",
                "description": "List all processed cases (paginated)",
            },
            "statistics": {
                "method": "GET",
                "path": "/loan/statistics",
                "description": "Get system statistics and analytics",
            },
            "test": {
                "method": "POST",
                "path": "/loan/test",
                "description": "Test with sample application data",
            },
            "docs": {
                "method": "GET",
                "path": "/docs",
                "description": "Interactive API documentation (Swagger UI)",
            },
            "openapi": {
                "method": "GET",
                "path": "/openapi.json",
                "description": "OpenAPI schema",
            },
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
