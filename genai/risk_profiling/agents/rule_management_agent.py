import os
from groq import Groq
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class RuleManagementAgent:
    def __init__(self):
        # Initialize Groq LLM with Gemma model
        self.llm = ChatGroq(
            model="gemma2-9b-it",
            temperature=0.2,
            max_tokens=1024,
        )
        
        # Create rule update prompt using from_messages instead of from_template
        self.rule_update_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in financial risk management and rule creation. Your task is to analyze a transaction and its risk assessment to determine if the current rule base needs to be updated."""),
            ("user", """Current Rule Base:
{rule_base}

Transaction Data:
{transaction_data}

Risk Assessment:
{risk_assessment}

If you believe the rule base should be updated, provide a new rule in the following format:
Rule X: If [condition], add risk score [score], category "[category]", factor "[risk factor description]"

For example:
Rule 6: If transaction_amount > 75000 and account_age_days < 60, add risk score 85, category "High", factor "Large transaction from relatively new account"

If no update is needed, respond with "No rule update needed."

Make sure your rule is clear, specific, and doesn't duplicate existing rules.
             
note: just create or update the rule, dont give additional explaination of changes or anything else""")
        ])
        
        # Create the chain
        self.chain = self.rule_update_prompt | self.llm | StrOutputParser()
    
    def _get_rules_file_path(self):
        """
        Get the path to the rules file
        """
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "rules", "rules.txt")
    
    def update_rules(self, transaction, risk_profile):
        """
        Update the rule base based on the transaction and risk assessment
        """
        # Only proceed if rule update is needed
        if not risk_profile.get('rule_update_needed', False):
            return False
        
        # Get current rule base
        rules_file = self._get_rules_file_path()
        with open(rules_file, 'r') as f:
            current_rules = f.read()
        
        # Run the LLM chain
        try:
            # Convert transaction and risk_profile to strings if they're not already
            transaction_str = str(transaction.to_dict()) if hasattr(transaction, 'to_dict') else str(transaction)
            risk_assessment_str = str(risk_profile)
            
            result = self.chain.invoke({
                "transaction_data": transaction_str,
                "risk_assessment": risk_assessment_str,
                "rule_base": current_rules
            })
            
            # Check if we got a valid rule update
            if result and "Rule" in result and "No rule update needed" not in result:
                # Add the new rule to the rule base
                with open(rules_file, 'a') as f:
                    f.write(f"\n{result}")
                return True
            
            return False
        except Exception as e:
            print(f"Error in rule update: {e}")
            return False