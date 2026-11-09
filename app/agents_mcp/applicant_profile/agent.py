from typing import Any


def run_applicant_profile_agent(application_data: dict) -> dict[str, Any]:
    """Mock applicant profile agent - returns realistic analysis without Claude API calls"""

    credit_score = application_data.get("credit_score", 650)
    employment_type = application_data.get("employment_type", "Salaried")
    income = application_data.get("income", 50000)
    age = application_data.get("age", 35)

    if credit_score >= 750:
        credit_summary = "Excellent credit profile with strong payment history"
        employment_risk = "LOW"
        score = 9.0
    elif credit_score >= 700:
        credit_summary = "Very good credit profile with consistent payments"
        employment_risk = "LOW"
        score = 8.0
    elif credit_score >= 650:
        credit_summary = "Good credit profile with minor payment issues"
        employment_risk = "MEDIUM"
        score = 7.0
    else:
        credit_summary = "Fair credit profile with payment concerns"
        employment_risk = "HIGH"
        score = 5.0

    if employment_type == "Salaried":
        score += 1.5
    elif employment_type == "Freelance":
        score -= 1.0

    if income >= 100000:
        score += 1.0
    elif income < 30000:
        score -= 2.0

    score = min(10.0, max(0.0, score))

    rating_idx = min(4, int(score / 2.5))
    ratings = ['weak', 'fair', 'good', 'strong', 'excellent']
    rating = ratings[rating_idx] if rating_idx < len(ratings) else 'adequate'

    output = {
        "completeness_status": "Complete",
        "income_stability_score": round(score, 1),
        "employment_risk": employment_risk,
        "credit_history_summary": credit_summary,
        "completeness_flags": [],
        "summary": f"Applicant demonstrates {rating} profile with {employment_type.lower()} employment.",
    }

    return output
