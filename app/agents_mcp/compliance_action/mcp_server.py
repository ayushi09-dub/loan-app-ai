import json
import uuid
from datetime import datetime
from typing import Any
from fastmcp import Server

server = Server("notification-system")

audit_trail = {}
case_database = {}


@server.call_tool()
def send_notification(
    applicant_id: str, decision: str, explanation: str
) -> dict[str, Any]:
    case_id = f"CASE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    notification = {
        "case_id": case_id,
        "applicant_id": applicant_id,
        "decision": decision,
        "explanation": explanation,
        "timestamp": datetime.now().isoformat(),
        "status": "SENT",
        "channels": ["EMAIL", "SYSTEM_LOG"],
    }

    case_database[case_id] = notification

    return {
        "success": True,
        "case_id": case_id,
        "message": f"Notification sent for applicant {applicant_id}",
        "timestamp": notification["timestamp"],
        "channels_notified": notification["channels"],
    }


@server.call_tool()
def record_audit_trail(case_id: str, all_agent_outputs: dict) -> dict[str, Any]:
    audit_entry = {
        "case_id": case_id,
        "timestamp": datetime.now().isoformat(),
        "agent_outputs": all_agent_outputs,
        "summary": {
            "applicant_profile": all_agent_outputs.get("profile_output", {}).get("summary", ""),
            "financial_risk": all_agent_outputs.get("risk_output", {}).get("summary", ""),
            "decision": all_agent_outputs.get("decision_output", {}).get("classification", "UNKNOWN"),
            "confidence": all_agent_outputs.get("decision_output", {}).get("confidence_level", 0),
        },
    }

    audit_trail[case_id] = audit_entry

    return {
        "success": True,
        "case_id": case_id,
        "message": f"Audit trail recorded for case {case_id}",
        "entries_recorded": len(audit_entry["agent_outputs"]),
        "audit_timestamp": audit_entry["timestamp"],
    }


@server.call_tool()
def get_case_status(case_id: str) -> dict[str, Any]:
    case = case_database.get(case_id, {})
    audit = audit_trail.get(case_id, {})

    if not case:
        return {
            "found": False,
            "message": f"Case {case_id} not found",
        }

    return {
        "found": True,
        "case_id": case_id,
        "applicant_id": case.get("applicant_id"),
        "decision": case.get("decision"),
        "status": case.get("status"),
        "timestamp": case.get("timestamp"),
        "audit_available": bool(audit),
        "channels_notified": case.get("channels", []),
    }


@server.call_tool()
def generate_compliance_report(case_id: str) -> dict[str, Any]:
    case = case_database.get(case_id, {})
    audit = audit_trail.get(case_id, {})

    if not case or not audit:
        return {
            "success": False,
            "message": f"Incomplete case or audit data for {case_id}",
        }

    report = {
        "case_id": case_id,
        "generated_at": datetime.now().isoformat(),
        "applicant_id": case.get("applicant_id"),
        "decision": case.get("decision"),
        "decision_timestamp": case.get("timestamp"),
        "audit_summary": audit.get("summary", {}),
        "compliance_status": "APPROVED",
        "review_ready": True,
    }

    return {
        "success": True,
        "report": report,
        "message": f"Compliance report generated for case {case_id}",
    }


@server.call_tool()
def log_application_event(
    case_id: str, event_type: str, event_data: dict
) -> dict[str, Any]:
    event = {
        "case_id": case_id,
        "event_type": event_type,
        "event_data": event_data,
        "timestamp": datetime.now().isoformat(),
        "logged": True,
    }

    return {
        "success": True,
        "event_id": uuid.uuid4().hex,
        "message": f"Event '{event_type}' logged for case {case_id}",
        "event": event,
    }


if __name__ == "__main__":
    server.run()
