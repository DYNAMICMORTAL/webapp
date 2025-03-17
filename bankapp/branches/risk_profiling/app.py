import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from agents.risk_assessment_agent import RiskAssessmentAgent
from agents.rule_management_agent import RuleManagementAgent
from agents.kyc_agent import KYCAgent
from utils.data_processor import load_sample_data

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Risk Profiling Dashboard",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS for a cleaner look
st.markdown("""
<style>
    .main {
        padding: 1rem 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        padding: 8px 16px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4a90e2;
        color: white;
    }
    .risk-high {
        color: #ff4b4b;
        font-weight: bold;
    }
    .risk-medium {
        color: #ffa500;
        font-weight: bold;
    }
    .risk-low {
        color: #00cc96;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize agents
@st.cache_resource
def load_agents():
    return {
        "risk_agent": RiskAssessmentAgent(),
        "rule_agent": RuleManagementAgent(),
        "kyc_agent": KYCAgent()
    }

def main():
    # App title
    st.title("Customer Risk Profiling Dashboard")
    
    # Sidebar for customer selection
    with st.sidebar:
        st.header("Customer Selection")
        customer_id = st.text_input("Enter Customer ID", value="20917")
        
        if st.button("Analyze Customer", type="primary"):
            st.session_state.run_analysis = True
            st.session_state.customer_id = customer_id
        
        st.divider()
        st.caption("Risk Profiling Dashboard v1.0")
    
    # Initialize session state
    if 'run_analysis' not in st.session_state:
        st.session_state.run_analysis = False
    
    if not st.session_state.run_analysis:
        # Display welcome message when no analysis is running
        st.info("Enter a customer ID and click 'Analyze Customer' to begin risk assessment.")
        return
    
    # Get agents
    agents = load_agents()
    risk_agent = agents["risk_agent"]
    kyc_agent = agents["kyc_agent"]
    
    # Display customer ID being analyzed
    st.subheader(f"Risk Assessment for Customer: {st.session_state.customer_id}")
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Profile Risk", "Transaction Risk", "Combined Assessment"])
    
    # Tab 1: Profile Risk Assessment
    with tab1:
        with st.spinner("Analyzing customer profile..."):
            profile_assessment = kyc_agent.analyze_customer_profile(st.session_state.customer_id)
        
        if "error" in profile_assessment:
            st.error(f"Error: {profile_assessment['error']}")
        else:
            # Customer profile from onboarding data
            if "kyc_data" in profile_assessment and "onboarding" in profile_assessment["kyc_data"]:
                onboarding_data = profile_assessment["kyc_data"]["onboarding"]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Customer Profile")
                    profile_table = []
                    
                    for key, value in onboarding_data.items():
                        if not isinstance(value, dict):
                            profile_table.append({"Field": key, "Value": value})
                    
                    st.table(pd.DataFrame(profile_table))
                
                # Additional nested data if available
                with col2:
                    for key, value in onboarding_data.items():
                        if isinstance(value, dict):
                            st.subheader(f"{key.title()}")
                            nested_table = []
                            for subkey, subvalue in value.items():
                                nested_table.append({"Field": subkey, "Value": subvalue})
                            st.table(pd.DataFrame(nested_table))
            
            # Profile risk assessment results
            profile_risk = profile_assessment["profile_risk"]
            
            # Create a card-like container for risk score
            st.subheader("Profile Risk Assessment")
            
            risk_color = "risk-low"
            if profile_risk['risk_category'] in ['High', 'Very High']:
                risk_color = "risk-high"
            elif profile_risk['risk_category'] == 'Medium':
                risk_color = "risk-medium"
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Risk Score", f"{profile_risk['risk_score']}/100")
            with col2:
                st.markdown(f"Risk Category: <span class='{risk_color}'>{profile_risk['risk_category']}</span>", 
                           unsafe_allow_html=True)
            
            # Risk factors
            st.subheader("Key Risk Factors")
            for factor in profile_risk['risk_factors']:
                st.markdown(f"- {factor}")
            
            # Explanation
            st.subheader("Explanation")
            st.write(profile_risk.get('explanation', 'No explanation provided'))
    
    # Tab 2: Transaction Risk Assessment
    with tab2:
        with st.spinner("Loading transaction data..."):
            transactions = load_sample_data(n_samples=5, customer_account=st.session_state.customer_id)
        
        if transactions.empty:
            st.error(f"No transactions found for customer {st.session_state.customer_id}")
            transaction_data = {"error": "No transactions found"}
        else:
            st.subheader(f"Transaction Analysis ({len(transactions)} transactions)")
            
            # Initialize risk counters
            high_risk_count = 0
            medium_risk_count = 0
            low_risk_count = 0
            total_risk_score = 0
            transaction_risks = []
            
            # Process each transaction with a progress bar
            progress_bar = st.progress(0)
            
            for idx, transaction in transactions.iterrows():
                # Update progress - Fix: Ensure progress is between 0.0 and 1.0
                progress = min(1.0, (idx + 1) / len(transactions))
                progress_bar.progress(progress)
                
                # Assess risk
                with st.spinner(f"Analyzing transaction {idx+1}/{len(transactions)}..."):
                    risk_profile = risk_agent.assess_risk(transaction)
                
                # Update risk counters
                total_risk_score += risk_profile['risk_score']
                if risk_profile['risk_category'] in ['High', 'Very High']:
                    high_risk_count += 1
                elif risk_profile['risk_category'] == 'Medium':
                    medium_risk_count += 1
                else:
                    low_risk_count += 1
                
                # Store transaction risk data
                transaction_risks.append({
                    "Transaction ID": transaction.get('transaction_id', f'TX-{idx}'),
                    "Risk Score": risk_profile['risk_score'],
                    "Risk Category": risk_profile['risk_category'],
                    "Risk Factors": risk_profile['risk_factors'],
                    "Explanation": risk_profile['explanation']
                })
            
            # Clear progress bar after completion
            progress_bar.empty()
            
            # Calculate overall transaction risk
            avg_risk_score = total_risk_score / len(transactions)
            
            # Prepare transaction data for combined assessment
            transaction_data = {
                "total_transactions": len(transactions),
                "high_risk_count": high_risk_count,
                "medium_risk_count": medium_risk_count,
                "low_risk_count": low_risk_count,
                "avg_risk_score": avg_risk_score
            }
            
            # Display transaction risk summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Risk Score", f"{avg_risk_score:.2f}/100")
            with col2:
                st.metric("High Risk Transactions", f"{high_risk_count}/{len(transactions)}")
            with col3:
                st.metric("Medium Risk Transactions", f"{medium_risk_count}/{len(transactions)}")
            
            # Display individual transaction details in an expander
            st.subheader("Transaction Details")
            for idx, tx_risk in enumerate(transaction_risks):
                risk_color = "risk-low"
                if tx_risk['Risk Category'] in ['High', 'Very High']:
                    risk_color = "risk-high"
                elif tx_risk['Risk Category'] == 'Medium':
                    risk_color = "risk-medium"
                
                with st.expander(f"Transaction {idx+1}: {tx_risk['Transaction ID']} - " +
                                f"Risk: {tx_risk['Risk Category']}"):
                    st.markdown(f"**Risk Score:** {tx_risk['Risk Score']}")
                    st.markdown(f"**Risk Category:** <span class='{risk_color}'>{tx_risk['Risk Category']}</span>", 
                               unsafe_allow_html=True)
                    
                    st.markdown("**Risk Factors:**")
                    for factor in tx_risk['Risk Factors']:
                        st.markdown(f"- {factor}")
                    
                    st.markdown("**Explanation:**")
                    st.write(tx_risk['Explanation'])
    
    # Tab 3: Combined Risk Assessment
    with tab3:
        if "error" in profile_assessment or "error" in transaction_data:
            st.error("Cannot generate combined assessment due to errors in profile or transaction data.")
        else:
            with st.spinner("Generating combined risk assessment..."):
                # Get combined risk assessment
                combined_assessment = risk_agent.assess_combined_risk(
                    profile_assessment["profile_risk"], 
                    transaction_data
                )
            
            # Display combined risk assessment
            st.subheader("Combined Risk Assessment")
            
            risk_color = "risk-low"
            if combined_assessment['risk_category'] in ['High', 'Very High']:
                risk_color = "risk-high"
            elif combined_assessment['risk_category'] == 'Medium':
                risk_color = "risk-medium"
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Combined Risk Score", f"{combined_assessment['risk_score']}/100")
            with col2:
                st.markdown(f"Risk Category: <span class='{risk_color}'>{combined_assessment['risk_category']}</span>", 
                           unsafe_allow_html=True)
            
            # Risk factors
            st.subheader("Key Risk Factors")
            for factor in combined_assessment['risk_factors']:
                st.markdown(f"- {factor}")
            
            # Recommendation
            st.subheader("Recommendation")
            st.write(combined_assessment.get('recommendation', 'No recommendation provided'))
            
            # Add a visual indicator for overall risk
            st.subheader("Risk Summary")
            
            # Create a simple gauge chart using columns
            cols = st.columns(10)
            risk_score = combined_assessment['risk_score']
            
            for i in range(10):
                threshold = (i + 1) * 10
                if risk_score >= threshold:
                    if threshold <= 30:
                        color = "#00cc96"  # Green for low risk
                    elif threshold <= 70:
                        color = "#ffa500"  # Orange for medium risk
                    else:
                        color = "#ff4b4b"  # Red for high risk
                    
                    cols[i].markdown(f"""
                    <div style="background-color: {color}; height: 20px; border-radius: 2px;"></div>
                    """, unsafe_allow_html=True)
                else:
                    cols[i].markdown("""
                    <div style="background-color: #e6e6e6; height: 20px; border-radius: 2px;"></div>
                    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 