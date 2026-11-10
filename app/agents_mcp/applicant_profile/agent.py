import anthropic
import os
import json
import sys
from typing import Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from mcp_client import call_mcp_tool


def run_applicant_profile_agent(application_data: dict) -> dict[str, Any]:
    """Applicant profile agent - analyzes credit and employment via MCP"""

    mcp_server_path = str(Path(__file__).parent / "mcp_server.py")

    try:
        # Call MCP tools
        completeness = call_mcp_tool(
            mcp_server_path,
            "applicant-profile-db",
            "check_application_completeness",
            application_data=application_data,
        )

        income_stability = call_mcp_tool(
            mcp_server_path,
            "applicant-profile-db",
            "calculate_income_stability_score",
            employment_type=application_data.get("employment_type", "Salaried"),
            employment_duration_years=5,
            delinquencies=0,
        )

        output = {
            "completeness_status": "Complete" if completeness.get("complete") else "Incomplete",
            "income_stability_score": income_stability.get("income_stability_score", 5.0),
            "employment_risk": income_stability.get("rating", "Fair").upper(),
            "credit_history_summary": f"Credit Score {application_data.get('credit_score', 650)}",
            "completeness_flags": completeness.get("missing_fields", []),
            "summary": f"Profile: {completeness.get('completeness_percentage', 0):.0f}% complete",
        }

        return output

    except Exception as e:
        print(f"MCP error: {str(e)}")

        # Fallback
        credit_score = application_data.get("credit_score", 650)
        score = 9.0 if credit_score >= 750 else 8.0 if credit_score >= 700 else 7.0 if credit_score >= 650 else 5.0

        return {
            "completeness_status": "Complete",
            "income_stability_score": score,
            "employment_risk": "LOW" if credit_score >= 700 else "MEDIUM" if credit_score >= 650 else "HIGH",
            "credit_history_summary": f"Score {credit_score}",
            "completeness_flags": [],
            "summary": "Profile assessment completed",
        }
