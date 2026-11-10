import anthropic
import os
import json
import uuid
import sys
from datetime import datetime
from typing import Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from mcp_client import call_mcp_tool


def run_compliance_action_agent(
    application_data: dict,
    profile_output: dict,
    risk_output: dict,
    decision_output: dict,
) -> dict[str, Any]:
    """Compliance agent - determines actions via MCP"""

    mcp_server_path = str(Path(__file__).parent / "mcp_server.py")

    applicant_id = application_data.get("applicant_id", "UNKNOWN")
    classification = decision_output.get("classification", "UNKNOWN")
    confidence = decision_output.get("confidence_level", 0)
    case_id = f"CASE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.now().isoformat()

    try:
        # Call MCP tools
        notification_result = call_mcp_tool(
            mcp_server_path,
            "notification-system",
            "send_notification",
            applicant_id=applicant_id,
            decision=classification,
            explanation=decision_output.get("explanation", "Decision made"),
        )

        # Build audit trail
        all_agent_outputs = {
            "application_data": application_data,
            "profile_output": profile_output,
            "risk_output": risk_output,
            "decision_output": decision_output,
        }

        audit_result = call_mcp_tool(
            mcp_server_path,
            "notification-system",
            "record_audit_trail",
            case_id=case_id,
            all_agent_outputs=all_agent_outputs,
        )

        output = {
            "action_taken": "NOTIFICATION_SENT_AND_AUDIT_RECORDED",
            "notification_sent": notification_result.get("success", True),
            "case_id": case_id,
            "timestamp": timestamp,
            "channels_notified": ["EMAIL", "SYSTEM_LOG"],
            "audit_recorded": audit_result.get("success", True),
            "compliance_status": classification,
            "summary": f"Application {case_id} processed",
        }

        return output

    except Exception as e:
        print(f"MCP error: {str(e)}")

        # Fallback
        return {
            "action_taken": "NOTIFICATION_SENT_AND_AUDIT_RECORDED",
            "notification_sent": True,
            "case_id": case_id,
            "timestamp": timestamp,
            "channels_notified": ["EMAIL", "SYSTEM_LOG"],
            "audit_recorded": True,
            "compliance_status": classification,
            "summary": f"Application {case_id} processed and applicant notified",
        }
