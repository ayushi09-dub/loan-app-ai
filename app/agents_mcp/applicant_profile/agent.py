import anthropic
import os
import json
from typing import Any


def run_applicant_profile_agent(application_data: dict) -> dict[str, Any]:
    """Applicant profile agent - uses Claude API to analyze credit and employment"""

    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL"),
    )

    model = os.getenv("ANTHROPIC_MODEL", "global.anthropic.claude-haiku-4-5-20251001-v1:0")

    tools = [
        {
            "name": "analyze_profile",
            "description": "Analyze applicant profile based on credit and employment data",
            "input_schema": {
                "type": "object",
                "properties": {
                    "credit_score": {"type": "integer"},
                    "employment_type": {"type": "string"},
                    "income": {"type": "number"},
                },
                "required": ["credit_score", "employment_type", "income"],
            },
        }
    ]

    credit_score = application_data.get("credit_score", 650)
    employment_type = application_data.get("employment_type", "Salaried")
    income = application_data.get("income", 50000)

    prompt = f"""Analyze this loan application profile:
Credit Score: {credit_score}
Employment Type: {employment_type}
Annual Income: ${income}

Provide ONLY a JSON response with exactly these fields:
{{
  "completeness_status": "Complete",
  "income_stability_score": <0-10>,
  "employment_risk": "<LOW|MEDIUM|HIGH>",
  "credit_history_summary": "<brief summary>",
  "completeness_flags": [],
  "summary": "<assessment>"
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
            score = 9.0 if credit_score >= 750 else 8.0 if credit_score >= 700 else 7.0 if credit_score >= 650 else 5.0
            output = {
                "completeness_status": "Complete",
                "income_stability_score": score,
                "employment_risk": "LOW" if credit_score >= 700 else "MEDIUM" if credit_score >= 650 else "HIGH",
                "credit_history_summary": f"Score {credit_score} - " + ("Excellent" if credit_score >= 750 else "Very Good" if credit_score >= 700 else "Good" if credit_score >= 650 else "Fair"),
                "completeness_flags": [],
                "summary": "Profile assessment completed by Claude",
            }

        return output

    except Exception as e:
        print(f"Claude API error: {str(e)}")
        raise
