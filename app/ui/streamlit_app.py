import streamlit as st
import httpx
import json
from datetime import datetime
from typing import Optional

st.set_page_config(
    page_title="Loan Approval System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .decision-approved {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .decision-rejected {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .decision-review {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .risk-high {
        color: #dc3545;
        font-weight: bold;
    }
    .risk-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .risk-low {
        color: #28a745;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🏦 Intelligent Loan Approval System</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI-Powered Multi-Agent Loan Analysis & Decision</p>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.markdown("### 📋 Application Details")

    applicant_id = st.text_input(
        "Applicant ID",
        value="APP-001",
        help="Unique identifier for the applicant"
    )

    age = st.slider("Age", min_value=18, max_value=80, value=35)

    income = st.number_input(
        "Annual Income ($)",
        min_value=20000,
        max_value=500000,
        value=75000,
        step=5000
    )

    employment_type = st.selectbox(
        "Employment Type",
        ["Salaried", "Self-Employed", "Freelance", "Retired", "Other"]
    )

    credit_score = st.slider(
        "Credit Score",
        min_value=300,
        max_value=850,
        value=750,
        help="Higher is better"
    )

    loan_amount = st.number_input(
        "Loan Amount ($)",
        min_value=10000,
        max_value=1000000,
        value=250000,
        step=10000
    )

    tenure_months = st.slider(
        "Loan Tenure (months)",
        min_value=12,
        max_value=360,
        value=60,
        step=12
    )

    existing_liabilities = st.number_input(
        "Existing Liabilities ($)",
        min_value=0,
        max_value=500000,
        value=50000,
        step=5000
    )

    location = st.selectbox(
        "Location",
        ["New York", "California", "Texas", "Florida", "Illinois", "Other"]
    )

    st.markdown("---")
    submit_button = st.button(
        "🚀 Submit Application",
        use_container_width=True,
        type="primary"
    )

with col2:
    st.markdown("### 📊 Analysis Results")

    if submit_button:
        st.session_state.submitted = True

    if st.session_state.get("submitted", False):
        with st.spinner("Processing application through AI agents..."):
            try:
                payload = {
                    "applicant_id": applicant_id,
                    "age": age,
                    "income": income,
                    "employment_type": employment_type,
                    "credit_score": credit_score,
                    "loan_amount": loan_amount,
                    "tenure_months": tenure_months,
                    "existing_liabilities": existing_liabilities,
                    "location": location,
                }

                response = httpx.post("http://localhost:8000/loan/apply", json=payload, timeout=30)

                if response.status_code == 200:
                    result = response.json()
                    st.session_state.result = result
                else:
                    st.error(f"API Error: {response.status_code}")

            except httpx.ConnectError:
                st.warning("⚠️ Backend API not available. Showing mock results for demonstration.")
                st.session_state.result = {
                    "success": True,
                    "case_id": "CASE-DEMO-12345",
                    "classification": "APPROVED",
                    "risk_score": 3.2,
                    "confidence_level": 94,
                    "explanation": "Application approved based on analysis (demo mode).",
                    "full_analysis": {
                        "profile_output": {"income_stability_score": 8.5, "employment_risk": "LOW"},
                        "risk_output": {"dti_ratio": 28.5, "credit_score_risk": "LOW"},
                        "decision_output": {"key_factors": ["Strong income", "Good credit"]},
                        "compliance_output": {"case_id": "CASE-DEMO-12345"},
                    }
                }
            except Exception as e:
                st.error(f"Error: {str(e)}")

        if "result" in st.session_state:
            result = st.session_state.result
            full_analysis = result.get("full_analysis", {})
            profile = full_analysis.get("profile_output", {})
            risk = full_analysis.get("risk_output", {})
            decision = full_analysis.get("decision_output", {})
            compliance = full_analysis.get("compliance_output", {})

            st.markdown("#### Step-by-Step Analysis")

            with st.expander("👤 **Applicant Profile Analysis**", expanded=True):
                st.info(f"""
                **Agent:** Applicant Profile Agent

                - ✅ Income Stability Score: {profile.get('income_stability_score', 'N/A')}/10
                - ✅ Employment Risk: {profile.get('employment_risk', 'N/A')}
                - ✅ Credit History: {profile.get('credit_history_summary', 'Excellent (750+)')}
                - ✅ Application Completeness: {profile.get('completeness_status', '100%')}
                """)

            with st.expander("💰 **Financial Risk Assessment**", expanded=True):
                dti_value = risk.get('dti_ratio', 28.5)
                if dti_value < 36:
                    dti_status = "Healthy"
                elif dti_value < 43:
                    dti_status = "Acceptable"
                else:
                    dti_status = "High Risk"
                st.info(f"""
                **Agent:** Financial Risk Analysis Agent

                - 📊 Debt-to-Income Ratio: {dti_value}% ({dti_status})
                - 📈 Credit Risk Level: {risk.get('credit_score_risk', 'LOW')}
                - 💵 Loan Amount Risk: {risk.get('loan_amount_risk', 'ACCEPTABLE')}
                - 🚨 Anomaly Flags: {', '.join(risk.get('anomaly_flags', [])) or 'NONE'}
                """)

            with st.expander("🎯 **Loan Decision**", expanded=True):
                st.info(f"""
                **Agent:** Loan Decision Agent

                - Classification: {result.get('classification', 'PENDING')}
                - Risk Score: {result.get('risk_score', 'N/A')}/10
                - Confidence: {result.get('confidence_level', 'N/A')}%
                - Key Factors: {', '.join(decision.get('key_factors', []))}
                """)

            with st.expander("✅ **Compliance & Action**", expanded=True):
                st.info(f"""
                **Agent:** Compliance & Action Orchestrator

                - Action Taken: {compliance.get('action_taken', 'N/A')}
                - Case ID: {result.get('case_id', 'N/A')}
                - Timestamp: {result.get('timestamp', 'N/A')}
                - Status: {compliance.get('compliance_status', 'PROCESSED')}
                """)

            st.markdown("---")

            classification = result.get("classification", "UNKNOWN")
            if classification == "APPROVED":
                decision_class = "decision-approved"
                decision_text = "✅ APPROVED"
            elif classification == "REJECTED":
                decision_class = "decision-rejected"
                decision_text = "❌ REJECTED"
            else:
                decision_class = "decision-review"
                decision_text = "🔄 MANUAL REVIEW"

            st.markdown(f'<div class="{decision_class}"><h3>{decision_text}</h3></div>', unsafe_allow_html=True)

            col_metric1, col_metric2, col_metric3 = st.columns(3)

            with col_metric1:
                risk_score = result.get("risk_score", 5)
                risk_color = "#28a745" if risk_score <= 3.5 else "#ffc107" if risk_score <= 6 else "#dc3545"
                risk_label = "Low Risk" if risk_score <= 3.5 else "Medium Risk" if risk_score <= 6 else "High Risk"
                risk_class = "risk-low" if risk_score <= 3.5 else "risk-medium" if risk_score <= 6 else "risk-high"
                st.markdown(f"""
                <div class="metric-card">
                    <strong>Risk Score</strong><br>
                    <span style="font-size: 2rem; color: {risk_color};">{risk_score} / 10</span>
                    <br><span class="{risk_class}">{risk_label}</span>
                </div>
                """, unsafe_allow_html=True)

            with col_metric2:
                st.markdown(f"""
                <div class="metric-card">
                    <strong>Confidence Level</strong><br>
                    <span style="font-size: 2rem; color: #1f77b4;">{result.get('confidence_level', 'N/A')}%</span>
                </div>
                """, unsafe_allow_html=True)

            with col_metric3:
                dti = risk.get("dti_ratio", 28.5)
                if dti < 36:
                    dti_color = "#28a745"
                    dti_status = "Healthy"
                elif dti < 43:
                    dti_color = "#ffc107"
                    dti_status = "Acceptable"
                else:
                    dti_color = "#dc3545"
                    dti_status = "High Risk"
                st.markdown(f"""
                <div class="metric-card">
                    <strong>DTI Ratio</strong><br>
                    <span style="font-size: 2rem; color: {dti_color};">{dti}%</span>
                    <br><span style="color: {dti_color}; font-weight: bold;">{dti_status}</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 📋 Summary")
            st.write(f"""
            **Decision:** The loan application has been **{classification}** based on comprehensive multi-agent analysis.

            **Explanation:**
            {result.get('explanation', 'N/A')}

            **Case Details:**
            - **Case ID:** {result.get('case_id', 'N/A')}
            - **Decision Date:** {datetime.now().strftime('%Y-%m-%d')}
            - **Timestamp:** {result.get('timestamp', 'N/A')}
            """)

            with st.expander("📄 **Full Audit Trail**"):
                st.json(result.get("full_analysis", {}))

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ System Info")
st.sidebar.info("""
**Multi-Agent Architecture:**
- 🤖 4 Specialized AI Agents
- 🔗 MCP Servers for data access
- 📊 LangGraph Orchestration
- 🚀 FastAPI Backend

**Supported Decisions:**
- ✅ Approved
- ❌ Rejected
- 🔄 Manual Review
""")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Backend Status")
try:
    response = httpx.get("http://localhost:8000/health", timeout=2)
    if response.status_code == 200:
        st.sidebar.success("✅ API Backend: Connected")
    else:
        st.sidebar.warning("⚠️ API Backend: Disconnected")
except:
    st.sidebar.warning("⚠️ API Backend: Not Running")

st.sidebar.markdown("---")
st.sidebar.caption("Version 1.0 | Powered by Claude Sonnet 4.6")
