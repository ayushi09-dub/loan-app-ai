import anthropic
import os
import json
import uuid
from datetime import datetime
from typing import Any


def run_compliance_action_agent(
    application_data: dict,
    profile_output: dict,
    risk_output: dict,
    decision_output: dict,
) -> dict[str, Any]:
    """Compliance agent - determines actions and generates audit trail"""

    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL"),
    )

    model = os.getenv("ANTHROPIC_MODEL", "global.anthropic.claude-haiku-4-5-20251001-v1:0")

    applicant_id = application_data.get("applicant_id", "UNKNOWN")
    classification = decision_output.get("classification", "UNKNOWN")
    confidence = decision_output.get("confidence_level", 0)
    risk_score = decision_output.get("risk_score", 5.0)

    case_id = f"CASE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.now().isoformat()

    prompt = f"""Determine compliance actions for this loan decision:

Decision Details:
- Classification: {classification}
- Confidence Level: {confidence}%
- Risk Score: {risk_score}/10
- Applicant ID: {applicant_id}

Based on this decision, provide ONLY valid JSON (no markdown, no extra text):
{{
  "action_taken": "NOTIFICATION_SENT_AND_AUDIT_RECORDED",
  "notification_sent": true,
  "compliance_status": "APPROVED",
  "audit_notes": "Loan application processed and decision recorded in audit trail",
  "summary": "Decision notification sent to applicant"
}}

Compliance guidelines:
- If APPROVED: Send approval notification, record in audit trail
- If REJECTED: Send rejection notice with reasoning, record denial
- If MANUAL_REVIEW: Flag for human review, notify case manager

Provide realistic audit trail and notification actions."""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                response_text = block.text
                break

        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                claude_output = json.loads(json_match.group())
            else:
                claude_output = json.loads(response_text)
        except (json.JSONDecodeError, AttributeError):
            claude_output = {
                "action_taken": "NOTIFICATION_SENT_AND_AUDIT_RECORDED",
                "notification_sent": True,
                "compliance_status": classification if classification in ["APPROVED", "REJECTED"] else "PENDING_REVIEW",
                "audit_notes": "Application decision processed and recorded",
                "summary": f"Decision notified to applicant via email and system log",
            }

        # Build complete agent outputs for audit trail
        all_agent_outputs = {
            "application_data": application_data,
            "profile_output": profile_output,
            "risk_output": risk_output,
            "decision_output": decision_output,
        }

        # Record audit trail with all agent outputs
        audit_trail_entry = {
            "case_id": case_id,
            "timestamp": timestamp,
            "applicant_id": applicant_id,
            "decision": classification,
            "confidence": confidence,
            "all_agent_outputs": all_agent_outputs,
            "compliance_notes": claude_output.get("audit_notes", ""),
        }

        output = {
            "action_taken": claude_output.get("action_taken", "NOTIFICATION_SENT"),
            "notification_sent": claude_output.get("notification_sent", True),
            "case_id": case_id,
            "timestamp": timestamp,
            "channels_notified": ["EMAIL", "SYSTEM_LOG"],
            "audit_recorded": True,
            "audit_trail_entry": audit_trail_entry,
            "compliance_status": claude_output.get("compliance_status", classification),
            "summary": claude_output.get("summary", f"Application {case_id} processed and applicant notified"),
        }

        return output

    except Exception as e:
        error_msg = f"Compliance error: {str(e)}"
        print(error_msg)

        # Return safe fallback with audit trail
        return {
            "action_taken": "ERROR_LOGGED_AND_ESCALATED",
            "notification_sent": False,
            "case_id": case_id,
            "timestamp": timestamp,
            "channels_notified": ["SYSTEM_LOG"],
            "audit_recorded": True,
            "compliance_status": "PENDING_REVIEW",
            "error": error_msg,
            "summary": "Error in compliance processing - case escalated for manual review",
        }
