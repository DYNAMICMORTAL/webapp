import os
import json
from groq import Groq
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
import pandas as pd

class TransactionRiskAgent:
    def __init__(self):
        """Initialize the Transaction Risk Agent with Groq's Gemma model and RAG capabilities."""
        # Initialize the LLM
        self.llm = ChatGroq(
            model="gemma2-9b-it",
            temperature=0.1,
            max_tokens=1024,
        )
        
        # Initialize embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        
        # Load vector database
        self.vector_db = self._load_vector_db()
        
        # Create the prompt template
        self.prompt_template = self._create_prompt_template()
    
    def _load_vector_db(self):
        """Load the vector database."""
        vector_db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "vector_db"
        )
        
        # Check if vector DB exists
        if not os.path.exists(vector_db_path):
            raise FileNotFoundError(
                "Vector database not found. Please run setup_vector_db.py first."
            )
        
        # Load the existing vector store
        return Chroma(
            persist_directory=vector_db_path,
            embedding_function=self.embeddings
        )
    
    def _retrieve_relevant_knowledge(self, transaction):
        """
        Retrieve relevant knowledge from the vector database based on transaction details.
        
        Args:
            transaction (dict): Transaction data
            
        Returns:
            dict: Retrieved knowledge organized by category
        """
        # Format transaction as a query string
        query = ""
        for key, value in transaction.items():
            if pd.notna(value) and value is not None and value != "":
                query += f"{key}: {value}, "
        
        # Add specific queries based on transaction details
        specific_queries = []
        
        # Add country-specific queries if countries are present
        if "source_country" in transaction and pd.notna(transaction["source_country"]):
            specific_queries.append(f"risks related to {transaction['source_country']}")
        
        if "destination_country" in transaction and pd.notna(transaction["destination_country"]):
            specific_queries.append(f"risks related to {transaction['destination_country']}")
        
        # Add amount-specific queries if amount is present
        if "amount" in transaction and pd.notna(transaction["amount"]):
            specific_queries.append(f"transaction patterns for amount {transaction['amount']}")
        
        # Add transaction type queries if present
        if "transaction_type" in transaction and pd.notna(transaction["transaction_type"]):
            specific_queries.append(f"risks for {transaction['transaction_type']} transactions")
        
        # Combine the general query with specific queries
        all_queries = [query] + specific_queries
        
        # Retrieve documents for each query and combine results
        retrieved_knowledge = {
            "jurisdictional_risks": "",
            "regulatory_frameworks": "",
            "transaction_patterns": ""
        }
        
        # Set of already retrieved document IDs to avoid duplicates
        retrieved_ids = set()
        
        for query in all_queries:
            # Retrieve relevant documents
            docs = self.vector_db.similarity_search(query, k=5)
            
            for doc in docs:
                # Generate a unique ID for the document
                doc_id = f"{doc.metadata['source']}_{doc.metadata['chunk_id']}"
                
                # Skip if already retrieved
                if doc_id in retrieved_ids:
                    continue
                
                retrieved_ids.add(doc_id)
                
                # Add content to the appropriate category
                category = doc.metadata["category"]
                if category in retrieved_knowledge:
                    retrieved_knowledge[category] += doc.page_content + "\n\n"
        
        return retrieved_knowledge
    
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
        Analyze a cross-border transaction for risk factors using RAG approach.
        
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
        
        # Retrieve relevant knowledge from vector DB
        retrieved_knowledge = self._retrieve_relevant_knowledge(transaction)

        print(f"Retrived Knowledge: {retrieved_knowledge}")
        
        # Combine with retrieved knowledge
        prompt_data = {
            "transaction_details": transaction_details,
            **retrieved_knowledge
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