import anthropic
import os
import json
from typing import Any


def run_applicant_profile_agent(application_data: dict) -> dict[str, Any]:
    """Applicant profile agent - analyzes credit and employment data"""

    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL"),
    )

    model = os.getenv("ANTHROPIC_MODEL", "global.anthropic.claude-haiku-4-5-20251001-v1:0")

    credit_score = application_data.get("credit_score", 650)
    employment_type = application_data.get("employment_type", "Salaried")
    income = application_data.get("income", 50000)
    age = application_data.get("age", 35)

    prompt = f"""Analyze this loan application profile and provide assessment:

Applicant Details:
- Age: {age}
- Annual Income: ${income:,.2f}
- Employment Type: {employment_type}
- Credit Score: {credit_score}

Evaluate and respond with ONLY valid JSON (no markdown, no extra text):
{{
  "completeness_status": "Complete",
  "income_stability_score": 8.5,
  "employment_risk": "LOW",
  "credit_history_summary": "Strong credit profile",
  "completeness_flags": [],
  "summary": "Solid applicant profile based on available data"
}}

Base your assessment on:
1. Income Stability Score (0-10): Higher for salaried employees, lower for freelance
2. Employment Risk: LOW for stable employment, MEDIUM for some variability, HIGH for unstable
3. Credit History Summary: Based on the credit score provided
4. Completeness Flags: Any missing or concerning information

Use realistic values based on the data provided."""

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
                "summary": "Profile assessment completed",
            }

        return output

    except Exception as e:
        print(f"Claude API error: {str(e)}")
        raise
