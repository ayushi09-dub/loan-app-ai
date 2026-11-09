import anthropic
import os
import json
from typing import Any


def run_financial_risk_agent(application_data: dict) -> dict[str, Any]:
    """Financial risk agent - evaluates financial metrics and risk factors"""

    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL"),
    )

    model = os.getenv("ANTHROPIC_MODEL", "global.anthropic.claude-haiku-4-5-20251001-v1:0")

    income = application_data.get("income", 50000)
    liabilities = application_data.get("existing_liabilities", 0)
    loan_amount = application_data.get("loan_amount", 100000)
    credit_score = application_data.get("credit_score", 650)
    tenure_months = application_data.get("tenure_months", 60)

    monthly_income = income / 12
    monthly_loan_payment = loan_amount / tenure_months
    monthly_debt = (liabilities / 12) + monthly_loan_payment
    dti_ratio = (monthly_debt / monthly_income * 100) if monthly_income > 0 else 0

    prompt = f"""Analyze the financial risk profile for this loan application:

Financial Details:
- Annual Income: ${income:,.2f}
- Existing Liabilities: ${liabilities:,.2f}
- Requested Loan Amount: ${loan_amount:,.2f}
- Loan Tenure: {tenure_months} months
- Credit Score: {credit_score}
- Calculated DTI Ratio: {dti_ratio:.1f}%

Provide risk assessment as ONLY valid JSON (no markdown, no extra text):
{{
  "dti_ratio": 35.5,
  "credit_score_risk": "LOW",
  "loan_amount_risk": "ACCEPTABLE",
  "anomaly_flags": [],
  "overall_risk_score": 3.5,
  "reasoning": "Strong income, manageable DTI, acceptable loan-to-income ratio",
  "summary": "Financial profile shows acceptable risk levels"
}}

Evaluation criteria:
- DTI Ratio < 36% = Healthy, 36-43% = Acceptable, > 43% = High Risk
- Credit Score >= 750 = LOW risk, 650-749 = MEDIUM risk, < 650 = HIGH risk
- Loan-to-Income: <= 3x annual income = ACCEPTABLE, 3-5x = MODERATE, > 5x = HIGH
- Risk Score: 0-3 = Low, 3-6 = Medium, 6-10 = High

Use realistic assessment based on the data."""

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
                "summary": "Financial analysis completed",
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
