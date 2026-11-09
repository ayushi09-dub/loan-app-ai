from typing import Any


def run_loan_decision_agent(
    application_data: dict, profile_output: dict, risk_output: dict
) -> dict[str, Any]:
    """Mock loan decision agent - returns realistic decision without Claude API calls"""

    profile_score = profile_output.get("income_stability_score", 5.0)
    risk_score = risk_output.get("overall_risk_score", 5.0)
    dti_ratio = risk_output.get("dti_ratio", 50.0)

    decision_score = (profile_score * 0.4) + ((10 - risk_score) * 0.6)

    if decision_score >= 7.5 and risk_score <= 3.5 and dti_ratio < 43:
        classification = "APPROVED"
        confidence = min(95, int(70 + (decision_score - 7.5) * 5))
    elif decision_score >= 5.5 and risk_score <= 6.0 and dti_ratio < 50:
        classification = "MANUAL_REVIEW"
        confidence = int(60 + (decision_score - 5.5) * 3)
    else:
        classification = "REJECTED"
        confidence = int(70 + (6.0 - decision_score) * 3)

    key_factors = []
    if profile_score >= 8:
        key_factors.append(f"Strong income stability ({profile_score}/10)")
    if risk_score <= 2:
        key_factors.append("Excellent financial profile")
    if dti_ratio < 36:
        key_factors.append(f"Healthy DTI ratio ({dti_ratio:.1f}%)")
    if not risk_output.get("anomaly_flags"):
        key_factors.append("No detected anomalies")

    if not key_factors:
        key_factors = ["Application meets minimum criteria"]

    if classification == "APPROVED":
        explanation = f"Application APPROVED based on comprehensive analysis. Applicant demonstrates strong financial health with a risk score of {risk_score}/10. Decision confidence: {confidence}%."
    elif classification == "MANUAL_REVIEW":
        explanation = f"Application requires MANUAL REVIEW. While some positive factors are present, the risk assessment ({risk_score}/10) warrants human evaluation. Decision confidence: {confidence}%."
    else:
        explanation = f"Application REJECTED. The risk assessment ({risk_score}/10) and financial metrics indicate significant concerns. Decision confidence: {confidence}%."

    output = {
        "classification": classification,
        "risk_score": risk_score,
        "confidence_level": confidence,
        "key_factors": key_factors,
        "explanation": explanation,
        "next_steps": (
            ["Final compliance check", "Send approval notification", "Prepare loan documents"]
            if classification == "APPROVED"
            else ["Human review required", "Request additional documentation"]
        ),
        "summary": f"{classification} - Risk Score: {risk_score}/10",
    }

    return output
