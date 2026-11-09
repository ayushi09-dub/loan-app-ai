import pytest
import httpx
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agents_mcp.applicant_profile.agent import run_applicant_profile_agent
from app.agents_mcp.financial_risk.agent import run_financial_risk_agent
from app.agents_mcp.loan_decision.agent import run_loan_decision_agent
from app.agents_mcp.compliance_action.agent import run_compliance_action_agent


sample_application = {
    "applicant_id": "TEST-001",
    "age": 35,
    "income": 75000,
    "employment_type": "Salaried",
    "credit_score": 750,
    "loan_amount": 250000,
    "tenure_months": 60,
    "existing_liabilities": 50000,
    "location": "New York",
}


class TestApplicantProfileAgent:
    def test_run_agent(self):
        """Test applicant profile agent execution"""
        result = run_applicant_profile_agent(sample_application)

        assert "income_stability_score" in result
        assert "employment_risk" in result
        assert "completeness_status" in result
        assert result["income_stability_score"] > 0

    def test_profile_output_structure(self):
        """Test that agent returns expected output structure"""
        result = run_applicant_profile_agent(sample_application)

        required_fields = [
            "income_stability_score",
            "employment_risk",
            "credit_history_summary",
            "completeness_flags",
            "summary",
        ]

        for field in required_fields:
            assert field in result, f"Missing field: {field}"


class TestFinancialRiskAgent:
    def test_run_agent(self):
        """Test financial risk agent execution"""
        result = run_financial_risk_agent(sample_application)

        assert "dti_ratio" in result
        assert "credit_score_risk" in result
        assert "overall_risk_score" in result
        assert 0 <= result["overall_risk_score"] <= 10

    def test_risk_output_structure(self):
        """Test that agent returns expected output structure"""
        result = run_financial_risk_agent(sample_application)

        required_fields = [
            "dti_ratio",
            "credit_score_risk",
            "loan_amount_risk",
            "anomaly_flags",
            "overall_risk_score",
        ]

        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_dti_calculation(self):
        """Test DTI ratio is calculated reasonably"""
        result = run_financial_risk_agent(sample_application)

        dti = result["dti_ratio"]
        assert isinstance(dti, (int, float))
        assert 0 <= dti <= 100


class TestLoanDecisionAgent:
    def test_run_agent(self):
        """Test loan decision agent execution"""
        profile = run_applicant_profile_agent(sample_application)
        risk = run_financial_risk_agent(sample_application)
        result = run_loan_decision_agent(sample_application, profile, risk)

        assert "classification" in result
        assert result["classification"] in ["APPROVED", "REJECTED", "MANUAL_REVIEW"]
        assert "risk_score" in result
        assert "confidence_level" in result

    def test_decision_classification_valid(self):
        """Test that decision classification is valid"""
        profile = run_applicant_profile_agent(sample_application)
        risk = run_financial_risk_agent(sample_application)
        result = run_loan_decision_agent(sample_application, profile, risk)

        valid_classifications = ["APPROVED", "REJECTED", "MANUAL_REVIEW"]
        assert result["classification"] in valid_classifications


class TestComplianceAgent:
    def test_run_agent(self):
        """Test compliance agent execution"""
        profile = run_applicant_profile_agent(sample_application)
        risk = run_financial_risk_agent(sample_application)
        decision = run_loan_decision_agent(sample_application, profile, risk)
        result = run_compliance_action_agent(
            sample_application, profile, risk, decision
        )

        assert "case_id" in result
        assert "action_taken" in result
        assert result["notification_sent"] is True

    def test_compliance_output_structure(self):
        """Test that agent returns expected output structure"""
        profile = run_applicant_profile_agent(sample_application)
        risk = run_financial_risk_agent(sample_application)
        decision = run_loan_decision_agent(sample_application, profile, risk)
        result = run_compliance_action_agent(
            sample_application, profile, risk, decision
        )

        required_fields = [
            "action_taken",
            "notification_sent",
            "case_id",
            "timestamp",
        ]

        for field in required_fields:
            assert field in result, f"Missing field: {field}"


class TestEndToEndWorkflow:
    def test_full_loan_application_flow(self):
        """Test the complete loan application workflow"""
        profile = run_applicant_profile_agent(sample_application)
        assert profile is not None

        risk = run_financial_risk_agent(sample_application)
        assert risk is not None

        decision = run_loan_decision_agent(sample_application, profile, risk)
        assert decision is not None
        assert decision["classification"] in ["APPROVED", "REJECTED", "MANUAL_REVIEW"]

        compliance = run_compliance_action_agent(
            sample_application, profile, risk, decision
        )
        assert compliance is not None
        assert "case_id" in compliance

    def test_workflow_with_high_risk_applicant(self):
        """Test workflow with high-risk applicant"""
        high_risk_app = sample_application.copy()
        high_risk_app["credit_score"] = 450
        high_risk_app["existing_liabilities"] = 200000
        high_risk_app["income"] = 30000

        profile = run_applicant_profile_agent(high_risk_app)
        risk = run_financial_risk_agent(high_risk_app)
        decision = run_loan_decision_agent(high_risk_app, profile, risk)

        assert decision["risk_score"] > 5 or decision["classification"] != "APPROVED"


class TestEdgeCases:
    def test_missing_fields_handling(self):
        """Test handling of incomplete applications"""
        incomplete_app = {
            "applicant_id": "TEST-INCOMPLETE",
            "age": 35,
            "income": 75000,
        }

        profile = run_applicant_profile_agent(incomplete_app)
        assert "completeness_flags" in profile

    def test_extreme_age(self):
        """Test with extreme age values"""
        elderly_app = sample_application.copy()
        elderly_app["age"] = 80

        result = run_financial_risk_agent(elderly_app)
        assert result is not None

    def test_very_high_loan_amount(self):
        """Test with very high loan amount"""
        high_loan_app = sample_application.copy()
        high_loan_app["loan_amount"] = 5000000
        high_loan_app["income"] = 50000

        result = run_financial_risk_agent(high_loan_app)
        assert result["overall_risk_score"] > 5


@pytest.mark.asyncio
class TestAPIEndpoints:
    @pytest.fixture
    async def client(self):
        from app.api.main import app

        async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "endpoints" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
