import anthropic
import os
import json
import sys
from typing import Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from mcp_client import call_mcp_tool


def run_loan_decision_agent(
    application_data: dict, profile_output: dict, risk_output: dict
) -> dict[str, Any]:
    """Loan decision agent - synthesizes decision via MCP"""

    mcp_server_path = str(Path(__file__).parent / "mcp_server.py")

    try:
        # Call MCP tool
        decision_result = call_mcp_tool(
            mcp_server_path,
            "decision-synthesis",
            "synthesize_decision",
            profile_output=profile_output,
            risk_output=risk_output,
        )

        output = {
            "classification": decision_result.get("classification", "MANUAL_REVIEW"),
            "risk_score": decision_result.get("risk_score", 5.0),
            "confidence_level": decision_result.get("confidence_level", 60),
            "key_factors": decision_result.get("key_factors", []),
            "explanation": decision_result.get("explanation", "Decision made"),
            "next_steps": decision_result.get("next_steps", []),
            "summary": decision_result.get("summary", "Decision processed"),
        }

        return output

    except Exception as e:
        print(f"MCP error: {str(e)}")

        # Fallback decision logic
        profile_score = profile_output.get("income_stability_score", 5.0)
        risk_score = risk_output.get("overall_risk_score", 5.0)
        dti_ratio = risk_output.get("dti_ratio", 50.0)
        credit_risk = risk_output.get("credit_score_risk", "MEDIUM")

        if profile_score >= 7 and risk_score <= 3 and dti_ratio < 43 and credit_risk in ["LOW", "MEDIUM"]:
            classification = "APPROVED"
            confidence = 85
        elif profile_score < 5 or risk_score > 7 or dti_ratio > 50 or credit_risk == "HIGH":
            classification = "REJECTED"
            confidence = 70
        else:
            classification = "MANUAL_REVIEW"
            confidence = 60

        return {
            "classification": classification,
            "risk_score": risk_score,
            "confidence_level": confidence,
            "key_factors": [f"Profile: {profile_score}/10", f"Risk: {risk_score}/10", f"DTI: {dti_ratio:.1f}%"],
            "explanation": "Decision made from analysis",
            "next_steps": ["Process application"],
            "summary": f"{classification}",
        }
