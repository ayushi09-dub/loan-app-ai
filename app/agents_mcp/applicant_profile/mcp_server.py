import json
from typing import Any
from pydantic import BaseModel

try:
    from fastmcp import Server
    server = Server("applicant-profile-db")
except ImportError:
    class FakeServer:
        def call_tool(self):
            def decorator(func):
                return func
            return decorator
    server = FakeServer()

applicant_database = {
    "APP-001": {
        "age": 35,
        "income": 75000,
        "employment_type": "Salaried",
        "employment_duration_years": 8,
        "credit_score": 750,
        "employment_stability": 0.95,
    },
    "APP-002": {
        "age": 28,
        "income": 45000,
        "employment_type": "Freelance",
        "employment_duration_years": 2,
        "credit_score": 680,
        "employment_stability": 0.60,
    },
}

credit_history_db = {
    "APP-001": {
        "credit_score": 750,
        "payment_history": "Excellent",
        "accounts_count": 5,
        "avg_account_age_years": 8,
        "delinquencies": 0,
        "hard_inquiries_6m": 0,
    },
    "APP-002": {
        "credit_score": 680,
        "payment_history": "Good",
        "accounts_count": 3,
        "avg_account_age_years": 4,
        "delinquencies": 1,
        "hard_inquiries_6m": 2,
    },
}


@server.call_tool()
def get_applicant_profile(applicant_id: str) -> dict[str, Any]:
    profile = applicant_database.get(applicant_id, {})
    return {
        "found": bool(profile),
        "data": profile,
        "message": f"Profile for {applicant_id} retrieved" if profile else "Profile not found",
    }


@server.call_tool()
def get_credit_history(applicant_id: str) -> dict[str, Any]:
    history = credit_history_db.get(applicant_id, {})
    return {
        "found": bool(history),
        "data": history,
        "message": f"Credit history for {applicant_id} retrieved" if history else "History not found",
    }


@server.call_tool()
def check_application_completeness(application_data: dict) -> dict[str, Any]:
    required_fields = [
        "applicant_id",
        "age",
        "income",
        "employment_type",
        "credit_score",
        "loan_amount",
        "tenure_months",
        "existing_liabilities",
        "location",
    ]

    missing_fields = [field for field in required_fields if field not in application_data]
    completeness_score = (
        (len(required_fields) - len(missing_fields)) / len(required_fields) * 100
    )

    return {
        "complete": len(missing_fields) == 0,
        "completeness_percentage": completeness_score,
        "missing_fields": missing_fields,
        "total_required": len(required_fields),
        "total_provided": len(required_fields) - len(missing_fields),
    }


@server.call_tool()
def calculate_income_stability_score(
    employment_type: str, employment_duration_years: int, delinquencies: int
) -> dict[str, Any]:
    score = 5.0

    employment_scores = {
        "Salaried": 3.0,
        "Self-Employed": -2.0,
        "Freelance": -2.5,
        "Retired": 1.0,
        "Other": -1.0,
    }
    score += employment_scores.get(employment_type, 0)

    if employment_duration_years >= 5:
        score += 2.0
    elif employment_duration_years >= 2:
        score += 1.0

    if delinquencies == 0:
        score += 1.5
    elif delinquencies == 1:
        score -= 1.0
    else:
        score -= 3.0

    score = max(0.0, min(10.0, score))

    return {
        "income_stability_score": round(score, 1),
        "rating": "Excellent" if score >= 8 else "Good" if score >= 6 else "Fair" if score >= 4 else "Poor",
        "factors": {
            "employment_type": employment_type,
            "employment_duration_years": employment_duration_years,
            "delinquencies": delinquencies,
        },
    }


if __name__ == "__main__":
    server.run()
