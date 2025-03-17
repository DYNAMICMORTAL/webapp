import os
import pandas as pd
from dotenv import load_dotenv
from agents.risk_assessment_agent import RiskAssessmentAgent
from agents.rule_management_agent import RuleManagementAgent
from agents.kyc_agent import KYCAgent
from utils.data_processor import load_sample_data

# Load environment variables
load_dotenv()

def main():
    # Initialize agents
    risk_agent = RiskAssessmentAgent()
    rule_agent = RuleManagementAgent()
    kyc_agent = KYCAgent()
    
    # Customer ID to analyze
    customer_id = "20917"
    
    print(f"{'='*80}")
    print(f"RISK ASSESSMENT FOR CUSTOMER: {customer_id}")
    print(f"{'='*80}")
    
    # 1. Profile Risk Assessment
    print("\nPROFILE RISK ASSESSMENT:")
    print(f"{'-'*50}")
    
    # Process KYC documents and assess profile risk
    profile_assessment = kyc_agent.analyze_customer_profile(customer_id)
    
    if "error" in profile_assessment:
        print(f"Error: {profile_assessment['error']}")
    else:
        # Display customer profile from onboarding data if available
        if "kyc_data" in profile_assessment and "onboarding" in profile_assessment["kyc_data"]:
            onboarding_data = profile_assessment["kyc_data"]["onboarding"]
            print("\nCustomer Profile (from onboarding data):")
            for key, value in onboarding_data.items():
                if isinstance(value, dict):
                    print(f"{key}:")
                    for subkey, subvalue in value.items():
                        print(f"  {subkey}: {subvalue}")
                else:
                    print(f"{key}: {value}")
        
        # Display profile risk assessment results
        profile_risk = profile_assessment["profile_risk"]
        print(f"\nProfile Risk Assessment Results:")
        print(f"Risk Score: {profile_risk['risk_score']}")
        print(f"Risk Category: {profile_risk['risk_category']}")
        print(f"Key Risk Factors:")
        for factor in profile_risk['risk_factors']:
            print(f"  - {factor}")
        print(f"\nExplanation: {profile_risk.get('explanation', 'No explanation provided')}")
    
    # 2. Transaction Risk Assessment
    print(f"\n{'='*80}")
    print("TRANSACTION RISK ASSESSMENT:")
    print(f"{'='*80}")
    
    # Load 5 random transactions for the specific customer
    transactions = load_sample_data(n_samples=5, customer_account=customer_id)
    
    if transactions.empty:
        print(f"No transactions found for customer {customer_id}")
        transaction_data = {"error": "No transactions found"}
    else:
        print(f"Processing {len(transactions)} sample transactions for risk assessment")
        
        # Track overall transaction risk
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0
        total_risk_score = 0
        
        # Process each transaction
        for idx, transaction in transactions.iterrows():
            print(f"\n{'-'*80}")
            print(f"Processing transaction {idx+1}/{len(transactions)}: {transaction.get('transaction_id', f'TX-{idx}')}")
            print(f"{'-'*80}")
            
            # Assess risk
            risk_profile = risk_agent.assess_risk(transaction)
            
            # Update risk counters
            total_risk_score += risk_profile['risk_score']
            if risk_profile['risk_category'] == 'High' or risk_profile['risk_category'] == 'Very High':
                high_risk_count += 1
            elif risk_profile['risk_category'] == 'Medium':
                medium_risk_count += 1
            else:
                low_risk_count += 1
            
            # Display risk assessment results
            print(f"\nRisk Assessment Results:")
            print(f"Risk Score: {risk_profile['risk_score']}")
            print(f"Risk Category: {risk_profile['risk_category']}")
            print(f"Key Risk Factors:")
            for factor in risk_profile['risk_factors']:
                print(f"  - {factor}")
            print(f"\nExplanation: {risk_profile['explanation']}")
        
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
    
    # 3. Combined Risk Assessment
    print(f"\n{'='*80}")
    print("COMBINED RISK ASSESSMENT:")
    print(f"{'='*80}")
    
    # Use Gemini for combined assessment
    if "profile_risk" in profile_assessment and "error" not in transaction_data:
        # Get combined risk assessment
        combined_assessment = risk_agent.assess_combined_risk(
            profile_assessment["profile_risk"], 
            transaction_data
        )
        
        print(f"Combined Risk Score: {combined_assessment['risk_score']}")
        print(f"Combined Risk Category: {combined_assessment['risk_category']}")
        print(f"Key Risk Factors:")
        for factor in combined_assessment['risk_factors']:
            print(f"  - {factor}")
        print(f"\nRecommendation: {combined_assessment.get('recommendation', 'No recommendation provided')}")

if __name__ == "__main__":
    main()