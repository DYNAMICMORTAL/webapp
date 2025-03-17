import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd

class TransactionRiskAgent:
    def __init__(self):
        """Initialize the Transaction Risk Agent with Google's Generative AI."""
        # Initialize the LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0.1,
            google_api_key=os.environ.get("GOOGLE_API_KEY")
        )
        
        # Load knowledge base
        self.knowledge_base = self._load_knowledge_base()
        
        # Create the prompt template
        self.prompt_template = self._create_prompt_template()
    
    def _load_knowledge_base(self):
        """Load knowledge base files."""
        knowledge_base = {}
        kb_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_base")
        
        # Load jurisdictional risks
        try:
            with open(os.path.join(kb_dir, "jurisdictional_risks.md"), "r") as f:
                knowledge_base["jurisdictional_risks"] = f.read()
        except FileNotFoundError:
            knowledge_base["jurisdictional_risks"] = "Knowledge base file not found."
        
        # Load regulatory frameworks
        try:
            with open(os.path.join(kb_dir, "regulatory_frameworks.md"), "r") as f:
                knowledge_base["regulatory_frameworks"] = f.read()
        except FileNotFoundError:
            knowledge_base["regulatory_frameworks"] = "Knowledge base file not found."
        
        # Load transaction patterns
        try:
            with open(os.path.join(kb_dir, "transaction_patterns.md"), "r") as f:
                knowledge_base["transaction_patterns"] = f.read()
        except FileNotFoundError:
            knowledge_base["transaction_patterns"] = "Knowledge base file not found."
        
        return knowledge_base
    
    def _create_prompt_template(self):
        """Create the prompt template for transaction analysis."""
        system_template = """You are an expert financial crime analyst specializing in cross-border transaction monitoring. 
Your task is to analyze international payment transactions and assess their risk levels based on multiple factors.

Use the following knowledge base to inform your analysis:

## JURISDICTIONAL RISK INFORMATION
{jurisdictional_risks}

## REGULATORY FRAMEWORKS
{regulatory_frameworks}

## SUSPICIOUS TRANSACTION PATTERNS
{transaction_patterns}

For the transaction provided, conduct a comprehensive risk assessment with these three components:

1. JURISDICTIONAL RISK ASSESSMENT:
   - Evaluate the risk based on source and destination countries
   - Consider sanctions, corruption indices, and regulatory maturity
   - Assess currency risk and exchange control regulations
   - Provide a risk score (1-100) and risk level (Low, Medium, High, Very High)

2. ENTRY RISK ANALYSIS:
   - Analyze legitimacy of fund sources
   - Evaluate recipient profiles and risk factors
   - Consider business justification for transfers
   - Provide a risk score (1-100) and risk level (Low, Medium, High, Very High)

3. TRANSACTION PATTERN ANALYSIS:
   - Identify unusual transaction patterns
   - Detect structuring, smurfing, or other evasion techniques
   - Compare against known typologies of financial crime
   - Provide a risk score (1-100) and risk level (Low, Medium, High, Very High)

4. OVERALL RISK ASSESSMENT:
   - Calculate a combined risk score (1-100)
   - Determine overall risk category (Low, Medium, High, Very High)
   - List key risk factors (3-5 bullet points)
   - Provide recommendations for further action

Your response must be in JSON format with the following structure:
```json
{{
  "jurisdictional_risk": {{
    "risk_score": <1-100>,
    "risk_level": "<Low|Medium|High|Very High>",
    "analysis": "<detailed analysis>"
  }},
  "entry_risk": {{
    "risk_score": <1-100>,
    "risk_level": "<Low|Medium|High|Very High>",
    "analysis": "<detailed analysis>"
  }},
  "pattern_risk": {{
    "risk_score": <1-100>,
    "risk_level": "<Low|Medium|High|Very High>",
    "analysis": "<detailed analysis>"
  }},
  "overall_risk": {{
    "risk_score": <1-100>,
    "risk_category": "<Low|Medium|High|Very High>",
    "risk_factors": [
      "<factor 1>",
      "<factor 2>",
      "<factor 3>"
    ],
    "recommendations": "<detailed recommendations>"
  }}
}}
```

If any critical information is missing (like source/destination countries), assign a risk score of 75 and risk level of "High" due to the lack of transparency, and explain what information is missing and why it's important.
"""
        
        human_template = """Please analyze the following cross-border transaction:

Transaction Details:
{transaction_details}

Provide a comprehensive risk assessment in the required JSON format."""
        
        return ChatPromptTemplate.from_messages([
            ("system", system_template),
            ("human", human_template)
        ])
    
    def analyze_transaction(self, transaction):
        """
        Analyze a cross-border transaction for risk factors.
        
        Args:
            transaction (dict): Transaction data
            
        Returns:
            dict: Risk assessment results
        """
        # Format transaction details as a string
        transaction_details = ""
        for key, value in transaction.items():
            if pd.notna(value) and value is not None and value != "":
                transaction_details += f"- {key}: {value}\n"
        
        # Combine with knowledge base
        prompt_data = {
            "transaction_details": transaction_details,
            **self.knowledge_base
        }
        
        # Create the prompt
        prompt = self.prompt_template.format_messages(**prompt_data)
        
        # Get response from LLM
        response = self.llm.invoke(prompt)
        
        # Extract and parse JSON from response
        try:
            # Find JSON content in the response
            content = response.content
            
            # If the response contains markdown code blocks, extract the JSON
            if "```json" in content:
                json_content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_content = content.split("```")[1].split("```")[0].strip()
            else:
                json_content = content
            
            # Parse the JSON
            result = json.loads(json_content)
            return result
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw response: {response.content}")
            
            # Return a default structure in case of parsing error
            return {
                "jurisdictional_risk": {
                    "risk_score": 0,
                    "risk_level": "Error",
                    "analysis": f"Error parsing response: {e}"
                },
                "entry_risk": {
                    "risk_score": 0,
                    "risk_level": "Error",
                    "analysis": "Error parsing response"
                },
                "pattern_risk": {
                    "risk_score": 0,
                    "risk_level": "Error",
                    "analysis": "Error parsing response"
                },
                "overall_risk": {
                    "risk_score": 0,
                    "risk_category": "Error",
                    "risk_factors": ["Error parsing response"],
                    "recommendations": "Error parsing response"
                }
            } 