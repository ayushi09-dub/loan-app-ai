import anthropic
import os
import json
from typing import Any


def run_loan_decision_agent(
    application_data: dict, profile_output: dict, risk_output: dict
) -> dict[str, Any]:
    """Loan decision agent - synthesizes final loan decision from analysis"""

    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL"),
    )

    model = os.getenv("ANTHROPIC_MODEL", "global.anthropic.claude-haiku-4-5-20251001-v1:0")

    # Extract comprehensive profile and risk data
    profile_score = profile_output.get("income_stability_score", 5.0)
    employment_risk = profile_output.get("employment_risk", "MEDIUM")
    credit_summary = profile_output.get("credit_history_summary", "Unknown")
    completeness = profile_output.get("completeness_status", "Unknown")

    risk_score = risk_output.get("overall_risk_score", 5.0)
    dti_ratio = risk_output.get("dti_ratio", 50.0)
    credit_risk = risk_output.get("credit_score_risk", "MEDIUM")
    loan_amount_risk = risk_output.get("loan_amount_risk", "ACCEPTABLE")
    anomalies = risk_output.get("anomaly_flags", [])

    # Application context
    income = application_data.get("income", 0)
    credit_score = application_data.get("credit_score", 0)
    loan_amount = application_data.get("loan_amount", 0)

    prompt = f"""You are a loan approval decision maker. Synthesize this complete analysis:

APPLICANT PROFILE:
- Income Stability: {profile_score}/10 ({employment_risk})
- Credit History: {credit_summary}
- Application Status: {completeness}
- Annual Income: ${income:,.0f}
- Credit Score: {credit_score}

FINANCIAL RISK:
- Risk Score: {risk_score}/10
- DTI Ratio: {dti_ratio:.1f}% (Threshold: <36% healthy, <43% acceptable, >43% high)
- Credit Risk Level: {credit_risk}
- Loan Amount Risk: {loan_amount_risk}
- Loan Amount: ${loan_amount:,.0f}
- Anomalies Detected: {anomalies if anomalies else 'None'}

Make a final decision using ONLY valid JSON (no markdown, no extra text):
{{
  "classification": "APPROVED",
  "risk_score": 3.5,
  "confidence_level": 85,
  "key_factors": ["Factor 1", "Factor 2", "Factor 3"],
  "explanation": "Detailed reasoning for decision",
  "next_steps": ["Step 1", "Step 2"],
  "decision_rationale": "Comprehensive analysis"
}}

DECISION CRITERIA:
- APPROVED: Good profile (>=7), low risk (<=3), healthy DTI (<43%), and credit risk LOW/MEDIUM
- REJECTED: Poor profile (<5) OR very high risk (>7) OR excessive DTI (>50%) OR credit risk HIGH
- MANUAL_REVIEW: Borderline cases needing human review

Consider ALL factors holistically. Provide realistic, justified decision."""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=500,
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
                output = json.loads(json_match.group())
            else:
                output = json.loads(response_text)
        except (json.JSONDecodeError, AttributeError):
            # Decision logic based on all available data
            if profile_score >= 7 and risk_score <= 3 and dti_ratio < 43 and credit_risk in ["LOW", "MEDIUM"]:
                classification = "APPROVED"
                confidence = 85
                rationale = "Strong profile with manageable risk"
            elif profile_score < 5 or risk_score > 7 or dti_ratio > 50 or credit_risk == "HIGH":
                classification = "REJECTED"
                confidence = 70
                rationale = "Significant risk factors present"
            else:
                classification = "MANUAL_REVIEW"
                confidence = 60
                rationale = "Borderline case requires human judgment"

            output = {
                "classification": classification,
                "risk_score": risk_score,
                "confidence_level": confidence,
                "key_factors": [
                    f"Profile: {profile_score}/10",
                    f"Risk: {risk_score}/10",
                    f"DTI: {dti_ratio:.1f}%",
                    f"Credit Risk: {credit_risk}",
                ],
                "explanation": f"Decision made based on comprehensive analysis of profile, risk, and financial metrics",
                "next_steps": ["Notify applicant", "Process application"],
                "decision_rationale": rationale,
            }

        return output

    except Exception as e:
        error_msg = f"Decision error: {str(e)}"
        print(error_msg)

        # Safe fallback decision
        return {
            "classification": "MANUAL_REVIEW",
            "risk_score": risk_score,
            "confidence_level": 30,
            "key_factors": ["Error occurred", "Escalating to manual review"],
            "explanation": "Error in decision processing - case escalated",
            "next_steps": ["Manual review required"],
            "error": error_msg,
        }
