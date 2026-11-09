from typing import Any


def run_financial_risk_agent(application_data: dict) -> dict[str, Any]:
    """Mock financial risk agent - returns realistic analysis without Claude API calls"""

    income = application_data.get("income", 50000)
    liabilities = application_data.get("existing_liabilities", 0)
    loan_amount = application_data.get("loan_amount", 100000)
    credit_score = application_data.get("credit_score", 650)

    monthly_income = income / 12
    monthly_liabilities = liabilities / 12
    monthly_loan_payment = (loan_amount / 360) * 0.01
    total_debt = monthly_liabilities + monthly_loan_payment
    dti_ratio = (total_debt / monthly_income) * 100 if monthly_income > 0 else 0

    if credit_score >= 750:
        credit_risk = "LOW"
        risk_score = 1.5
    elif credit_score >= 700:
        credit_risk = "LOW"
        risk_score = 2.5
    elif credit_score >= 650:
        credit_risk = "MEDIUM"
        risk_score = 4.0
    else:
        credit_risk = "HIGH"
        risk_score = 7.0

    if loan_amount <= income * 2:
        loan_risk = "ACCEPTABLE"
    elif loan_amount <= income * 4:
        loan_risk = "MODERATE"
    else:
        loan_risk = "HIGH"

    anomalies = []
    if dti_ratio > 43:
        anomalies.append("DTI ratio exceeds recommended threshold")
        risk_score += 2.0
    if credit_score < 600:
        anomalies.append("Credit score below 600")
        risk_score += 1.5

    risk_score = min(10.0, max(0.0, risk_score))

    output = {
        "dti_ratio": round(dti_ratio, 1),
        "credit_score_risk": credit_risk,
        "loan_amount_risk": loan_risk,
        "anomaly_flags": anomalies,
        "overall_risk_score": round(risk_score, 1),
        "risk_scores": {
            "dti_ratio": round(dti_ratio, 1),
            "credit_risk": risk_score,
            "overall": round(risk_score, 1),
        },
        "reasoning": f"DTI of {dti_ratio:.1f}% is {'healthy' if dti_ratio < 36 else 'acceptable' if dti_ratio < 43 else 'elevated'}. Credit risk is {credit_risk}.",
        "summary": f"Financial analysis shows {'low' if risk_score <= 3 else 'moderate' if risk_score <= 6 else 'high'} overall risk profile.",
    }

    return output
