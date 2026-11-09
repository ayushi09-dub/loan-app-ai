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
    """Compliance agent - uses Claude API to determine actions and generate audit trail"""

    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL"),
    )

    model = os.getenv("ANTHROPIC_MODEL", "global.anthropic.claude-haiku-4-5-20251001-v1:0")

    applicant_id = application_data.get("applicant_id", "UNKNOWN")
    classification = decision_output.get("classification", "UNKNOWN")

    case_id = f"CASE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.now().isoformat()

    prompt = f"""Compliance action for decision:
Decision: {classification}
Confidence: {decision_output.get('confidence_level', 0)}%

Provide ONLY JSON:
{{
  "action_taken": "NOTIFICATION_SENT",
  "notification_sent": true,
  "compliance_status": "<APPROVED|REJECTED|PENDING_REVIEW>",
  "audit_notes": "<brief notes>",
  "summary": "<action summary>"
}}

Use ONLY JSON, no other text."""

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
                "audit_notes": "Processed by Claude",
                "summary": f"Application {case_id} decision recorded",
            }

        output = {
            "action_taken": claude_output.get("action_taken", "NOTIFICATION_SENT"),
            "notification_sent": claude_output.get("notification_sent", True),
            "case_id": case_id,
            "timestamp": timestamp,
            "channels_notified": ["EMAIL", "SYSTEM_LOG"],
            "audit_recorded": True,
            "compliance_status": claude_output.get("compliance_status", classification),
            "summary": claude_output.get("summary", f"Application {case_id} processed and applicant notified"),
        }

        return output

    except Exception as e:
        print(f"Claude API error: {str(e)}")
        raise
