import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from agents.transaction_risk_agent import TransactionRiskAgent
from utils.data_processor import load_transactions

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Cross-Border Transaction Risk Analysis",
    page_icon="🔍",
    layout="wide"
)

# App title and description
st.title("Cross-Border Transaction Risk Analysis")
st.markdown("This application analyzes cross-border transactions for potential risks and provides recommendations.")

# Initialize the transaction risk agent
@st.cache_resource
def get_risk_agent():
    return TransactionRiskAgent()

risk_agent = get_risk_agent()

# Sidebar for controls
st.sidebar.header("Controls")
num_samples = st.sidebar.slider("Number of transactions to analyze", 1, 10, 3)
analyze_button = st.sidebar.button("Load Random Transactions")

# Function to display transaction analysis
def display_transaction_analysis(transaction_dict, analysis_result, idx):
    with st.expander(f"Transaction #{idx+1} Details", expanded=True):
        # Create two columns for transaction details
        col1, col2 = st.columns(2)
        
        # Display transaction details
        with col1:
            st.subheader("Transaction Information")
            for key, value in transaction_dict.items():
                if pd.notna(value):  # Only display non-NA values
                    st.text(f"{key}: {value}")
        
        # Display analysis results
        with col2:
            st.subheader("Risk Analysis Results")
            
            # Jurisdictional Risk
            st.markdown("### 1. Jurisdictional Risk Assessment")
            jur_score = analysis_result['jurisdictional_risk']['risk_score']
            st.progress(min(jur_score/10, 1.0))  # Ensure value is between 0 and 1
            st.markdown(f"**Risk Score:** {jur_score}")
            st.markdown(f"**Risk Level:** {analysis_result['jurisdictional_risk']['risk_level']}")
            st.markdown(f"**Analysis:** {analysis_result['jurisdictional_risk']['analysis']}")
            
            # Entry Risk
            st.markdown("### 2. Entry Risk Analysis")
            entry_score = analysis_result['entry_risk']['risk_score']
            st.progress(min(entry_score/10, 1.0))  # Ensure value is between 0 and 1
            st.markdown(f"**Risk Score:** {entry_score}")
            st.markdown(f"**Risk Level:** {analysis_result['entry_risk']['risk_level']}")
            st.markdown(f"**Analysis:** {analysis_result['entry_risk']['analysis']}")
            
            # Pattern Risk
            st.markdown("### 3. Transaction Pattern Analysis")
            pattern_score = analysis_result['pattern_risk']['risk_score']
            st.progress(min(pattern_score/10, 1.0))  # Ensure value is between 0 and 1
            st.markdown(f"**Risk Score:** {pattern_score}")
            st.markdown(f"**Risk Level:** {analysis_result['pattern_risk']['risk_level']}")
            st.markdown(f"**Analysis:** {analysis_result['pattern_risk']['analysis']}")
        
        # Overall Risk Assessment (full width)
        st.markdown("### 4. Overall Risk Assessment")
        overall_score = analysis_result['overall_risk']['risk_score']
        
        # Color the progress bar based on risk level
        normalized_score = min(overall_score/10, 1.0)  # Ensure value is between 0 and 1
        if overall_score < 3:
            st.progress(normalized_score)  # Removed color parameter as it's not supported in this way
        elif overall_score < 7:
            st.progress(normalized_score)
        else:
            st.progress(normalized_score)
            
        st.markdown(f"**Combined Risk Score:** {overall_score}")
        st.markdown(f"**Risk Category:** {analysis_result['overall_risk']['risk_category']}")
        
        st.markdown("**Key Risk Factors:**")
        for factor in analysis_result['overall_risk']['risk_factors']:
            st.markdown(f"- {factor}")
        
        st.markdown(f"**Recommendations:** {analysis_result['overall_risk']['recommendations']}")

# Main app logic
if analyze_button:
    with st.spinner("Loading and analyzing transactions..."):
        # Load random transactions from the dataset
        transactions = load_transactions(n_samples=num_samples)
        
        if transactions.empty:
            st.error("No transactions loaded. Please check the data file.")
        else:
            # Process each transaction
            for idx, transaction in transactions.iterrows():
                # Convert transaction to dictionary for easier handling
                transaction_dict = transaction.to_dict()
                
                # Analyze transaction
                analysis_result = risk_agent.analyze_transaction(transaction_dict)
                
                # Display analysis
                display_transaction_analysis(transaction_dict, analysis_result, idx)
else:
    st.info("Click 'Load Random Transactions' to begin analysis.")

# Footer
st.markdown("---")
st.markdown("Cross-Border Transaction Risk Analysis Tool | Developed with Streamlit") 