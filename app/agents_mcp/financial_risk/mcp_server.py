from typing import Any

try:
    from fastmcp import Server
    server = Server("financial-risk-db")
except ImportError:
    class FakeServer:
        def call_tool(self):
            def decorator(func):
                return func
            return decorator
    server = FakeServer()

risk_thresholds = {
    "excellent": (751, 850),
    "very_good": (681, 750),
    "good": (601, 680),
    "fair": (501, 600),
    "poor": (300, 500),
}


@server.call_tool()
def calculate_dti(income: float, liabilities: float, loan_amount: float, tenure_months: int = 60) -> dict[str, Any]:
    monthly_income = income / 12
    monthly_liabilities = liabilities / 12

    # Calculate monthly loan payment using simple amortization
    # Assuming ~5% annual interest rate for standard loan
    annual_rate = 0.05
    monthly_rate = annual_rate / 12
    num_payments = tenure_months

    if monthly_rate > 0:
        monthly_loan_payment = (loan_amount * monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
    else:
        monthly_loan_payment = loan_amount / tenure_months

    total_monthly_debt = monthly_liabilities + monthly_loan_payment
    dti_ratio = (total_monthly_debt / monthly_income) * 100 if monthly_income > 0 else 0

    return {
        "dti_ratio": round(dti_ratio, 2),
        "monthly_income": round(monthly_income, 2),
        "monthly_liabilities": round(monthly_liabilities, 2),
        "monthly_loan_payment": round(monthly_loan_payment, 2),
        "monthly_debt": round(total_monthly_debt, 2),
        "status": "Healthy" if dti_ratio < 36 else "Acceptable" if dti_ratio < 43 else "High",
        "recommendation": "Good debt management" if dti_ratio < 36 else "Monitor carefully" if dti_ratio < 43 else "High risk",
    }


@server.call_tool()
def evaluate_credit_risk(credit_score: int) -> dict[str, Any]:
    risk_level = "Unknown"
    risk_score = 5.0

    for level, (min_score, max_score) in risk_thresholds.items():
        if min_score <= credit_score <= max_score:
            risk_level = level
            break

    if credit_score >= 751:
        risk_score = 1.0
    elif credit_score >= 681:
        risk_score = 2.0
    elif credit_score >= 601:
        risk_score = 3.5
    elif credit_score >= 501:
        risk_score = 6.5
    else:
        risk_score = 9.0

    return {
        "credit_score": credit_score,
        "risk_level": risk_level.upper(),
        "risk_score": risk_score,
        "approval_probability": max(0, 95 - (risk_score * 10)),
    }


@server.call_tool()
def detect_anomalies(
    application_data: dict,
) -> dict[str, Any]:
    anomalies = []

    if application_data.get("age", 0) < 21:
        anomalies.append("Age below 21 - may require special approval")

    if application_data.get("age", 0) > 75:
        anomalies.append("Age above 75 - retirement risk consideration")

    loan_income_ratio = application_data.get("loan_amount", 0) / max(
        application_data.get("income", 1), 1
    )
    if loan_income_ratio > 4:
        anomalies.append("Loan amount exceeds 4x annual income")

    dti_calc = calculate_dti(
        application_data.get("income", 1),
        application_data.get("existing_liabilities", 0),
        application_data.get("loan_amount", 0),
    )
    if dti_calc["dti_ratio"] > 50:
        anomalies.append("DTI ratio extremely high - major red flag")

    if application_data.get("credit_score", 0) < 500:
        anomalies.append("Very low credit score - high risk")

    return {
        "anomalies_detected": len(anomalies) > 0,
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "risk_level": "Critical" if len(anomalies) > 2 else "High" if len(anomalies) > 1 else "Low",
    }


@server.call_tool()
def calculate_loan_amount_risk(
    loan_amount: float, income: float, credit_score: int
) -> dict[str, Any]:
    loan_to_income = loan_amount / income

    if loan_to_income <= 2.5:
        risk_category = "Low"
        risk_score = 2.0
    elif loan_to_income <= 3.5:
        risk_category = "Medium"
        risk_score = 4.0
    elif loan_to_income <= 5:
        risk_category = "High"
        risk_score = 6.5
    else:
        risk_category = "Very High"
        risk_score = 8.5

    if credit_score >= 750:
        risk_score -= 1
    elif credit_score < 600:
        risk_score += 2

    risk_score = max(1.0, min(10.0, risk_score))

    return {
        "loan_to_income_ratio": round(loan_to_income, 2),
        "risk_category": risk_category,
        "risk_score": round(risk_score, 1),
    }


if __name__ == "__main__":
    server.run()
