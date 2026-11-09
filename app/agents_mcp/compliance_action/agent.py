import uuid
from datetime import datetime
from typing import Any


def run_compliance_action_agent(
    application_data: dict,
    profile_output: dict,
    risk_output: dict,
    decision_output: dict,
) -> dict[str, Any]:
    """Mock compliance agent - returns realistic compliance actions without Claude API calls"""

    applicant_id = application_data.get("applicant_id", "UNKNOWN")
    classification = decision_output.get("classification", "UNKNOWN")

    case_id = f"CASE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.now().isoformat()

    action_taken = "NOTIFICATION_SENT_AND_AUDIT_RECORDED"
    audit_recorded = True
    notification_sent = True
    channels = ["EMAIL", "SYSTEM_LOG"]

    if classification == "APPROVED":
        compliance_status = "APPROVED"
        summary = f"Application {case_id} has been APPROVED. Applicant notified. Audit trail recorded."
    elif classification == "REJECTED":
        compliance_status = "REJECTED"
        summary = f"Application {case_id} has been REJECTED. Applicant notified. Audit trail recorded."
    else:
        compliance_status = "PENDING_REVIEW"
        summary = f"Application {case_id} flagged for MANUAL REVIEW. Audit trail recorded for reviewer."

    output = {
        "action_taken": action_taken,
        "notification_sent": notification_sent,
        "case_id": case_id,
        "timestamp": timestamp,
        "channels_notified": channels,
        "audit_recorded": audit_recorded,
        "compliance_status": compliance_status,
        "summary": summary,
    }

    return output
