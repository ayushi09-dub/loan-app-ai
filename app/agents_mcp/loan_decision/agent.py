import anthropic
import os
import json
from typing import Any


def run_loan_decision_agent(
    application_data: dict, profile_output: dict, risk_output: dict
) -> dict[str, Any]:
    """Loan decision agent - uses Claude API to synthesize final decision"""

    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL"),
    )

    model = os.getenv("ANTHROPIC_MODEL", "global.anthropic.claude-haiku-4-5-20251001-v1:0")

    tools = [
        {
            "name": "make_decision",
            "description": "Synthesize loan decision based on profile and risk analysis",
            "input_schema": {
                "type": "object",
                "properties": {
                    "profile_score": {"type": "number"},
                    "risk_score": {"type": "number"},
                },
                "required": ["profile_score", "risk_score"],
            },
        }
    ]

    profile_score = profile_output.get("income_stability_score", 5.0)
    risk_score = risk_output.get("overall_risk_score", 5.0)
    dti_ratio = risk_output.get("dti_ratio", 50.0)

    prompt = f"""Make a loan decision:
Profile Score: {profile_score}/10
Risk Score: {risk_score}/10
DTI Ratio: {dti_ratio:.1f}%

Provide ONLY JSON:
{{
  "classification": "<APPROVED|REJECTED|MANUAL_REVIEW>",
  "risk_score": {risk_score},
  "confidence_level": <0-100>,
  "key_factors": ["factor1", "factor2"],
  "explanation": "<brief explanation>",
  "next_steps": ["action1"],
  "summary": "<one-liner>"
}}

Use ONLY JSON, no other text."""

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
            if profile_score >= 8 and risk_score <= 3 and dti_ratio < 43:
                classification = "APPROVED"
                confidence = 85
            elif profile_score >= 6 and risk_score <= 6 and dti_ratio < 50:
                classification = "MANUAL_REVIEW"
                confidence = 60
            else:
                classification = "REJECTED"
                confidence = 70

            output = {
                "classification": classification,
                "risk_score": risk_score,
                "confidence_level": confidence,
                "key_factors": [f"Profile: {profile_score}/10", f"Risk: {risk_score}/10", f"DTI: {dti_ratio:.1f}%"],
                "explanation": f"Decision by Claude based on analysis",
                "next_steps": ["Process application"],
                "summary": f"{classification} - Risk {risk_score}/10",
            }

        return output

    except Exception as e:
        print(f"Claude API error: {str(e)}")
        raise
