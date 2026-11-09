from typing import TypedDict, Any
from langgraph.graph import StateGraph, END
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents_mcp.applicant_profile.agent import run_applicant_profile_agent
from agents_mcp.financial_risk.agent import run_financial_risk_agent
from agents_mcp.loan_decision.agent import run_loan_decision_agent
from agents_mcp.compliance_action.agent import run_compliance_action_agent


class LoanState(TypedDict):
    application_data: dict
    profile_output: dict
    risk_output: dict
    decision_output: dict
    compliance_output: dict
    final_result: dict


def applicant_profile_node(state: LoanState) -> LoanState:
    """Run applicant profile analysis"""
    profile_output = run_applicant_profile_agent(state["application_data"])
    state["profile_output"] = profile_output
    return state


def financial_risk_node(state: LoanState) -> LoanState:
    """Run financial risk analysis"""
    risk_output = run_financial_risk_agent(state["application_data"])
    state["risk_output"] = risk_output
    return state


def loan_decision_node(state: LoanState) -> LoanState:
    """Run loan decision synthesis"""
    decision_output = run_loan_decision_agent(
        state["application_data"], state["profile_output"], state["risk_output"]
    )
    state["decision_output"] = decision_output
    return state


def compliance_node(state: LoanState) -> LoanState:
    """Run compliance and action orchestration"""
    compliance_output = run_compliance_action_agent(
        state["application_data"],
        state["profile_output"],
        state["risk_output"],
        state["decision_output"],
    )
    state["compliance_output"] = compliance_output

    state["final_result"] = {
        "case_id": compliance_output.get("case_id"),
        "classification": state["decision_output"].get("classification"),
        "risk_score": state["decision_output"].get("risk_score"),
        "confidence_level": state["decision_output"].get("confidence_level"),
        "explanation": state["decision_output"].get("explanation"),
        "profile_output": state["profile_output"],
        "risk_output": state["risk_output"],
        "decision_output": state["decision_output"],
        "compliance_output": compliance_output,
        "timestamp": compliance_output.get("timestamp"),
    }

    return state


def create_loan_graph():
    """Create LangGraph workflow"""
    workflow = StateGraph(LoanState)

    workflow.add_node("applicant_profile", applicant_profile_node)
    workflow.add_node("financial_risk", financial_risk_node)
    workflow.add_node("loan_decision", loan_decision_node)
    workflow.add_node("compliance", compliance_node)

    workflow.set_entry_point("applicant_profile")
    workflow.add_edge("applicant_profile", "financial_risk")
    workflow.add_edge("financial_risk", "loan_decision")
    workflow.add_edge("loan_decision", "compliance")
    workflow.add_edge("compliance", END)

    return workflow.compile()


def run_loan_application(application_data: dict) -> dict[str, Any]:
    """Execute the loan approval workflow"""
    graph = create_loan_graph()

    initial_state = LoanState(
        application_data=application_data,
        profile_output={},
        risk_output={},
        decision_output={},
        compliance_output={},
        final_result={},
    )

    result = graph.invoke(initial_state)

    return result["final_result"]
