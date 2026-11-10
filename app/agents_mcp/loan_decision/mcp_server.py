from typing import Any
try:
    from fastmcp import Server
except ImportError:
    class FakeServer:
        def call_tool(self):
            def decorator(func):
                return func
            return decorator

server = Server("decision-synthesis")


@server.call_tool()
def synthesize_decision(
    profile_output: dict, risk_output: dict, applicant_data: dict
) -> dict[str, Any]:
    profile_score = profile_output.get("income_stability_score", 5.0)
    risk_scores = risk_output.get("risk_scores", {})
    overall_risk = risk_scores.get("overall", 5.0)
    dti = risk_scores.get("dti_ratio", 50.0)
    credit_risk = risk_scores.get("credit_risk", 5.0)

    decision_score = (profile_score * 0.3) + ((10 - overall_risk) * 0.7)

    if decision_score >= 7.5 and overall_risk <= 3.5 and dti < 43:
        classification = "APPROVED"
        confidence = min(0.98, 0.75 + ((decision_score - 7.5) / 2.5 * 0.15))
    elif decision_score >= 5.5 and overall_risk <= 5.5 and dti < 50:
        classification = "MANUAL_REVIEW"
        confidence = 0.60 + ((decision_score - 5.5) / 2 * 0.15)
    else:
        classification = "REJECTED"
        confidence = min(0.95, 0.70 + ((5.5 - decision_score) / 5.5 * 0.15))

    key_factors = []
    if profile_score >= 8:
        key_factors.append("Strong income stability")
    if credit_risk <= 2:
        key_factors.append("Excellent credit profile")
    if dti < 36:
        key_factors.append("Low debt-to-income ratio")
    if overall_risk <= 3.5:
        key_factors.append("Low overall risk assessment")

    if decision_score < 5.5:
        key_factors = [
            "Low financial stability",
            "High risk profile",
            "Unfavorable debt ratios",
        ]

    return {
        "classification": classification,
        "risk_score": round(overall_risk, 1),
        "confidence_level": round(confidence * 100, 1),
        "decision_score": round(decision_score, 2),
        "key_factors": key_factors,
        "recommendation": f"Application {classification}. Confidence: {round(confidence * 100, 1)}%",
    }


@server.call_tool()
def generate_explanation(decision_data: dict) -> dict[str, Any]:
    classification = decision_data.get("classification", "UNKNOWN")
    risk_score = decision_data.get("risk_score", 5.0)
    confidence = decision_data.get("confidence_level", 0)
    key_factors = decision_data.get("key_factors", [])

    if classification == "APPROVED":
        base_explanation = "The application has been APPROVED based on comprehensive multi-agent analysis. "
        base_explanation += f"The applicant demonstrates strong financial health with a low risk score of {risk_score}/10. "
        base_explanation += f"Approval confidence is {confidence}%."
    elif classification == "MANUAL_REVIEW":
        base_explanation = "The application requires MANUAL REVIEW. "
        base_explanation += f"While some positive factors are present, the risk assessment ({risk_score}/10) and financial metrics warrant human evaluation. "
        base_explanation += f"Confidence level is {confidence}%."
    else:
        base_explanation = "The application has been REJECTED. "
        base_explanation += f"The risk assessment ({risk_score}/10) and financial analysis indicate significant concerns. "
        base_explanation += f"Confidence in rejection is {confidence}%."

    factors_text = "Key contributing factors: " + ", ".join(key_factors) if key_factors else ""

    full_explanation = base_explanation + factors_text

    return {
        "summary": base_explanation,
        "factors": factors_text,
        "full_explanation": full_explanation,
    }


@server.call_tool()
def calculate_approval_score(
    profile_stability: float,
    credit_score: int,
    dti_ratio: float,
    age: int,
    employment_type: str,
) -> dict[str, Any]:
    score = 50

    score += profile_stability * 5

    if credit_score >= 750:
        score += 20
    elif credit_score >= 700:
        score += 15
    elif credit_score >= 650:
        score += 10
    elif credit_score >= 600:
        score += 5
    else:
        score -= 10

    if dti_ratio < 30:
        score += 15
    elif dti_ratio < 40:
        score += 10
    elif dti_ratio < 50:
        score += 5
    else:
        score -= 15

    if 25 <= age <= 65:
        score += 5
    elif age > 70 or age < 21:
        score -= 10

    if employment_type in ["Salaried", "Retired"]:
        score += 5
    elif employment_type in ["Self-Employed", "Freelance"]:
        score -= 5

    score = max(0, min(100, score))

    return {
        "approval_score": round(score, 1),
        "score_range": "High" if score >= 70 else "Medium" if score >= 50 else "Low",
    }


if __name__ == "__main__":
    server.run()
