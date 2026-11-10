import anthropic
import os
import json
import sys
from typing import Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from mcp_client import call_mcp_tool


def run_financial_risk_agent(application_data: dict) -> dict[str, Any]:
    """Financial risk agent - evaluates financial metrics using MCP tools"""

    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL"),
    )

    model = os.getenv("ANTHROPIC_MODEL", "global.anthropic.claude-haiku-4-5-20251001-v1:0")

    # Get MCP server path
    mcp_server_path = str(Path(__file__).parent / "mcp_server.py")

    try:
        # Call MCP tools for financial analysis
        dti_result = call_mcp_tool(
            mcp_server_path,
            "financial-risk-db",
            "calculate_dti",
            income=application_data.get("income", 50000),
            liabilities=application_data.get("existing_liabilities", 0),
            loan_amount=application_data.get("loan_amount", 100000),
            tenure_months=application_data.get("tenure_months", 60),
        )

        credit_result = call_mcp_tool(
            mcp_server_path,
            "financial-risk-db",
            "evaluate_credit_risk",
            credit_score=application_data.get("credit_score", 650),
        )

        anomaly_result = call_mcp_tool(
            mcp_server_path,
            "financial-risk-db",
            "detect_anomalies",
            application_data=application_data,
        )

        # Combine MCP results
        output = {
            "dti_ratio": dti_result.get("dti_ratio", 0),
            "credit_score_risk": credit_result.get("risk_level", "UNKNOWN"),
            "loan_amount_risk": dti_result.get("status", "UNKNOWN"),
            "anomaly_flags": anomaly_result.get("anomalies", []),
            "overall_risk_score": credit_result.get("risk_score", 5.0),
            "reasoning": dti_result.get("recommendation", "Analysis completed"),
            "summary": "Financial analysis completed via MCP",
            "dti_status": dti_result.get("status"),
        }

        output["risk_scores"] = {
            "dti_ratio": output.get("dti_ratio", 0),
            "credit_risk": output.get("overall_risk_score", 5.0),
            "overall": output.get("overall_risk_score", 5.0),
        }

        return output

    except Exception as e:
        print(f"MCP error: {str(e)}")

        # Fallback to direct calculation if MCP fails
        income = application_data.get("income", 50000)
        liabilities = application_data.get("existing_liabilities", 0)
        loan_amount = application_data.get("loan_amount", 100000)
        credit_score = application_data.get("credit_score", 650)
        tenure_months = application_data.get("tenure_months", 60)

        monthly_income = income / 12
        monthly_loan_payment = loan_amount / tenure_months
        monthly_debt = (liabilities / 12) + monthly_loan_payment
        dti_ratio = (monthly_debt / monthly_income * 100) if monthly_income > 0 else 0

        risk = 1.5 if credit_score >= 750 else 3.0 if credit_score >= 700 else 5.0 if credit_score >= 650 else 7.0

        anomalies = []
        if application_data.get("age", 0) < 21:
            anomalies.append("Age below 21 - may require special approval")
        if application_data.get("age", 0) > 75:
            anomalies.append("Age above 75 - retirement risk consideration")
        if loan_amount / max(income, 1) > 4:
            anomalies.append("Loan amount exceeds 4x annual income")

        output = {
            "dti_ratio": round(dti_ratio, 1),
            "credit_score_risk": "LOW" if credit_score >= 700 else "MEDIUM" if credit_score >= 650 else "HIGH",
            "loan_amount_risk": "LOW" if loan_amount <= income * 2.5 else "MEDIUM" if loan_amount <= income * 3.5 else "HIGH" if loan_amount <= income * 5 else "VERY_HIGH",
            "anomaly_flags": anomalies,
            "overall_risk_score": risk,
            "reasoning": f"DTI {dti_ratio:.1f}% - Credit {credit_score}",
            "summary": "Financial analysis completed",
        }

        output["risk_scores"] = {
            "dti_ratio": output.get("dti_ratio", round(dti_ratio, 1)),
            "credit_risk": output.get("overall_risk_score", 5.0),
            "overall": output.get("overall_risk_score", 5.0),
        }

        return output
