import os
from groq import Groq
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json

class RiskAssessmentAgent:
    def __init__(self):
        # Initialize Groq LLM with Gemma model
        self.llm = ChatGroq(
            model="gemma2-9b-it",
            temperature=0.2,
            max_tokens=1024,
        )
        
        # Create risk assessment prompt with a completely revised format to avoid JSON parsing issues
        self.risk_assessment_prompt = ChatPromptTemplate.from_template("""
You are an expert financial risk assessment agent. Your task is to analyze transaction data and provide a comprehensive risk assessment.

Based on the transaction data and the current rule base, determine the risk level of the transaction.

Current Rule Base:
{rule_base}

Please analyze the following transaction data:
{transaction_data}

Provide a detailed risk assessment in JSON format. Include the following fields:
- risk_score: A number from 0-100
- risk_category: One of "Low", "Medium", "High", or "Very High"
- risk_factors: A list of specific risk factors identified
- explanation: A detailed explanation of the risk assessment
- rule_update_needed: A boolean indicating if rule base should be updated
- rule_update_suggestion: A suggestion for rule update if needed

Consider all aspects of the transaction including amount, timing, account history, and any anomalies.

Your response should be a valid JSON object.
note: give the json response without any addional headers like ``` or ```json.
""")
        
        # Create the chain
        self.chain = self.risk_assessment_prompt | self.llm | JsonOutputParser()
    
    def _get_rules(self):
        """
        Get rules from the text file
        """
        rules_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rules", "rules.txt")
        
        
        
        # Read rules from file
        with open(rules_file, 'r') as f:
            return f.read()
    
    def _apply_rules(self, transaction):
        """
        Apply simple rule-based checks to the transaction
        """
        rules = self._get_rules()
        risk_score = 0
        risk_factors = []
        risk_category = "Low"
        
        # Convert transaction to dict if it's a pandas Series
        if hasattr(transaction, 'to_dict'):
            transaction = transaction.to_dict()
        
        # Simple rule parsing and application
        for line in rules.split('\n'):
            line = line.strip()
            if not line or not line.startswith('Rule'):
                continue
            
            try:
                # Extract condition and actions
                parts = line.split(':', 1)[1].split(',')
                condition = parts[0].strip()
                
                # Extract risk score
                risk_score_part = [p for p in parts if 'risk score' in p][0]
                rule_risk_score = int(risk_score_part.split('risk score')[1].strip())
                
                # Extract category
                category_part = [p for p in parts if 'category' in p][0]
                rule_category = category_part.split('category')[1].strip().strip('"')
                
                # Extract factor
                factor_part = [p for p in parts if 'factor' in p][0]
                rule_factor = factor_part.split('factor')[1].strip().strip('"')
                
                # Evaluate condition
                if 'transaction_amount' in condition and '>' in condition:
                    threshold = float(condition.split('>')[1].strip())
                    condition_met = transaction['transaction_amount'] > threshold
                elif 'smurfing_indicator' in condition and '==' in condition:
                    value = int(condition.split('==')[1].strip())
                    condition_met = transaction['smurfing_indicator'] == value
                elif 'previous_fraud_flag' in condition and '==' in condition:
                    value = int(condition.split('==')[1].strip())
                    condition_met = transaction['previous_fraud_flag'] == value
                elif 'account_age_days' in condition and '<' in condition:
                    threshold = int(condition.split('<')[1].strip())
                    condition_met = transaction['account_age_days'] < threshold
                elif 'kyc_status' in condition and '==' in condition:
                    value = condition.split('==')[1].strip().strip("'")
                    condition_met = transaction['kyc_status'] == value
                else:
                    condition_met = False
                
                if condition_met:
                    # Update risk score if higher
                    risk_score = max(risk_score, rule_risk_score)
                    
                    # Add risk factor
                    risk_factors.append(rule_factor)
                    
                    # Update risk category if higher
                    category_levels = {"Low": 1, "Medium": 2, "High": 3, "Very High": 4}
                    if category_levels.get(rule_category, 0) > category_levels.get(risk_category, 0):
                        risk_category = rule_category
            
            except Exception as e:
                print(f"Error applying rule: {line}. Error: {e}")
        
        return {
            "risk_score": risk_score,
            "risk_category": risk_category,
            "risk_factors": risk_factors,
            "explanation": f"Rule-based assessment identified {len(risk_factors)} risk factors.",
            "rule_update_needed": False
        }
    
    def assess_risk(self, transaction):
        """
        Assess the risk of a transaction using the LLM and rule base
        """
        # Apply rule-based checks first
        rule_based_assessment = self._apply_rules(transaction)
        
        # Convert transaction to string representation
        transaction_str = json.dumps(transaction.to_dict(), indent=2)
        
        # Get current rule base as string
        rule_base_str = self._get_rules()
        
        # Run the LLM chain
        try:
            result = self.chain.invoke({
                "transaction_data": transaction_str,
                "rule_base": rule_base_str
            })
            
            # Combine rule-based assessment with LLM assessment
            if rule_based_assessment["risk_score"] > result["risk_score"]:
                result["risk_score"] = rule_based_assessment["risk_score"]
                result["risk_category"] = rule_based_assessment["risk_category"]
                result["risk_factors"].extend(rule_based_assessment["risk_factors"])
                
            return result
        except Exception as e:
            print(f"Error in risk assessment: {e}")
            # Fallback to rule-based assessment if LLM fails
            return rule_based_assessment

    def assess_combined_risk(self, profile_risk, transaction_data):
        """
        Assess combined risk based on profile risk and transaction risk data.
        
        Args:
            profile_risk: Dictionary containing profile risk assessment
            transaction_data: Dictionary containing transaction risk data
            
        Returns:
            Dictionary containing combined risk assessment
        """
        # Create a prompt for combined risk assessment
        combined_risk_prompt = ChatPromptTemplate.from_template("""
        You are an expert financial risk assessment agent. Your task is to provide a combined risk assessment based on both profile and transaction risk data.

        Analyze the following customer profile risk and transaction risk data:
        
        Profile Risk:
        {profile_risk}
        
        Transaction Risk:
        {transaction_data}
        
        Provide a combined risk assessment in JSON format with the following fields:
        - risk_score: A number from 0-100
        - risk_category: One of "Low", "Medium", "High", or "Very High"
        - risk_factors: A list of specific risk factors identified
        - recommendation: A recommendation for action based on the risk assessment
        
        Your response should be a valid JSON object.
        note: give the json response without any additional headers like ``` or ```json.
        """)
        
        # Create a chain for combined risk assessment
        combined_chain = combined_risk_prompt | self.llm | JsonOutputParser()
        
        # Run the chain
        try:
            result = combined_chain.invoke({
                "profile_risk": json.dumps(profile_risk, indent=2),
                "transaction_data": json.dumps(transaction_data, indent=2)
            })
            return result
        except Exception as e:
            print(f"Error in combined risk assessment: {e}")
            # Fallback if LLM fails
            return {
                "risk_score": (profile_risk.get("risk_score", 50) + transaction_data.get("avg_risk_score", 50)) / 2,
                "risk_category": "Medium",
                "risk_factors": ["Error in combined risk assessment"],
                "recommendation": "Manual review recommended due to assessment error"
            }