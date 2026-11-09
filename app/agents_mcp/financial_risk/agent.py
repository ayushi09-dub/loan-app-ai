import anthropic
import os
import json
from typing import Any


def run_financial_risk_agent(application_data: dict) -> dict[str, Any]:
    """Financial risk agent - uses Claude API to evaluate financial metrics"""

    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL"),
    )

    model = os.getenv("ANTHROPIC_MODEL", "global.anthropic.claude-haiku-4-5-20251001-v1:0")

    tools = [
        {
            "name": "evaluate_risk",
            "description": "Evaluate financial risk based on income, liabilities, and loan amount",
            "input_schema": {
                "type": "object",
                "properties": {
                    "income": {"type": "number"},
                    "liabilities": {"type": "number"},
                    "loan_amount": {"type": "number"},
                },
                "required": ["income", "liabilities", "loan_amount"],
            },
        }
    ]

    income = application_data.get("income", 50000)
    liabilities = application_data.get("existing_liabilities", 0)
    loan_amount = application_data.get("loan_amount", 100000)
    credit_score = application_data.get("credit_score", 650)

    monthly_income = income / 12
    monthly_debt = liabilities / 12 + (loan_amount / 360)
    dti_ratio = (monthly_debt / monthly_income * 100) if monthly_income > 0 else 0

    prompt = f"""Analyze financial risk for this loan:
Income: ${income}
Existing Liabilities: ${liabilities}
Requested Loan: ${loan_amount}
Credit Score: {credit_score}
Calculated DTI: {dti_ratio:.1f}%

Provide ONLY JSON:
{{
  "dti_ratio": {dti_ratio:.1f},
  "credit_score_risk": "<LOW|MEDIUM|HIGH>",
  "loan_amount_risk": "<ACCEPTABLE|MODERATE|HIGH>",
  "anomaly_flags": [],
  "overall_risk_score": <0-10>,
  "reasoning": "<brief explanation>",
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
            risk = 1.5 if credit_score >= 750 else 3.0 if credit_score >= 700 else 5.0 if credit_score >= 650 else 7.0
            output = {
                "dti_ratio": round(dti_ratio, 1),
                "credit_score_risk": "LOW" if credit_score >= 700 else "MEDIUM" if credit_score >= 650 else "HIGH",
                "loan_amount_risk": "ACCEPTABLE" if loan_amount <= income * 3 else "MODERATE" if loan_amount <= income * 5 else "HIGH",
                "anomaly_flags": [],
                "overall_risk_score": risk,
                "reasoning": f"DTI {dti_ratio:.1f}% - Credit {credit_score}",
                "summary": "Financial analysis by Claude",
            }

        output["risk_scores"] = {
            "dti_ratio": output.get("dti_ratio", round(dti_ratio, 1)),
            "credit_risk": output.get("overall_risk_score", 5.0),
            "overall": output.get("overall_risk_score", 5.0),
        }

        return output

    except Exception as e:
        print(f"Claude API error: {str(e)}")
        raise
