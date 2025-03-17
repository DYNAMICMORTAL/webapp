import os
import pandas as pd
import random
from dotenv import load_dotenv
from agents.transaction_risk_agent import TransactionRiskAgent
from utils.data_processor import load_transactions

# Load environment variables
load_dotenv()

def main():
    # Initialize the transaction risk agent
    risk_agent = TransactionRiskAgent()
    
    # Load random transactions from the dataset (3 samples)
    transactions = load_transactions(n_samples=3)
    
    if transactions.empty:
        print("No transactions loaded. Please check the data file.")
        return
    
    # Process each transaction
    for idx, transaction in transactions.iterrows():
        print(f"\n{'='*80}")
        print(f"CROSS-BORDER TRANSACTION ANALYSIS #{idx}")
        print(f"{'='*80}")
        
        # Convert transaction to dictionary for easier handling
        transaction_dict = transaction.to_dict()
        
        # Display all available transaction details
        print("\nTransaction Details:")
        for key, value in transaction_dict.items():
            if pd.notna(value):  # Only print non-NA values
                print(f"{key}: {value}")
        
        # Analyze transaction
        analysis_result = risk_agent.analyze_transaction(transaction_dict)
        
        # Display analysis results
        print(f"\n{'-'*80}")
        print("ANALYSIS RESULTS:")
        print(f"{'-'*80}")
        
        print(f"\n1. Jurisdictional Risk Assessment:")
        print(f"Risk Score: {analysis_result['jurisdictional_risk']['risk_score']}")
        print(f"Risk Level: {analysis_result['jurisdictional_risk']['risk_level']}")
        print(f"Analysis: {analysis_result['jurisdictional_risk']['analysis']}")
        
        print(f"\n2. Entry Risk Analysis:")
        print(f"Risk Score: {analysis_result['entry_risk']['risk_score']}")
        print(f"Risk Level: {analysis_result['entry_risk']['risk_level']}")
        print(f"Analysis: {analysis_result['entry_risk']['analysis']}")
        
        print(f"\n3. Transaction Pattern Analysis:")
        print(f"Risk Score: {analysis_result['pattern_risk']['risk_score']}")
        print(f"Risk Level: {analysis_result['pattern_risk']['risk_level']}")
        print(f"Analysis: {analysis_result['pattern_risk']['analysis']}")
        
        print(f"\n4. Overall Risk Assessment:")
        print(f"Combined Risk Score: {analysis_result['overall_risk']['risk_score']}")
        print(f"Risk Category: {analysis_result['overall_risk']['risk_category']}")
        print(f"Key Risk Factors:")
        for factor in analysis_result['overall_risk']['risk_factors']:
            print(f"  - {factor}")
        print(f"\nRecommendations: {analysis_result['overall_risk']['recommendations']}")

if __name__ == "__main__":
    main() 