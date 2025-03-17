import os
import json
import random
from google import genai
from google.genai import types

class TransactionChatAssistant:
    def __init__(self):
        """Initialize the chat assistant with Gemini API."""
        # Look for either GEMINI_API_KEY or GOOGLE_API_KEY
        api_key = os.environ.get("GOOGLE_API_KEY")
        
        self.api_available = False
        
        if not api_key:
            print("WARNING: No API key found. Using fallback responses.")
            return
        
        try:
            self.client = genai.Client(api_key=api_key)
            self.model = "gemini-1.5-pro"  # Fallback to a standard model if 02-05 isn't available
            
            # Check available models and use the most appropriate one
            try:
                models = self.client.list_models()
                model_names = [model.name for model in models]
                
                # Try to use these models in order of preference
                preferred_models = [
                    "gemini-2.0-pro-exp-02-05", 
                    "gemini-1.5-pro", 
                    "gemini-1.0-pro"
                ]
                
                for model_name in preferred_models:
                    if any(model_name in name for name in model_names):
                        self.model = model_name
                        break
                
                self.api_available = True
                
            except Exception as e:
                print(f"Warning: Could not list models: {e}")
                # Still consider API available since we were able to create a client
                self.api_available = True
            
        except Exception as e:
            print(f"Error initializing Gemini client: {e}")
    
    def generate_response(self, query, transactions_data, customer_id):
        """
        Generate a response to a query about transaction data.
        
        Args:
            query (str): The user's query
            transactions_data (list): List of transaction dictionaries
            customer_id (str): The ID of the customer
            
        Returns:
            str: The assistant's response
        """
        # If API is not available, use fallback response
        if not self.api_available:
            return self._generate_fallback_response(query, transactions_data, customer_id)
            
        try:
            # Create prompt context with transaction data
            transactions_summary = self._create_transactions_summary(transactions_data)
            
            prompt = f"""You are a financial transaction assistant helping a customer analyze their transaction data.

CUSTOMER ID: {customer_id}

TRANSACTION DATA SUMMARY:
{transactions_summary}

USER QUERY: {query}

Please analyze the transaction data and respond to the user's query. 
Be precise, helpful, and use relevant transaction data to support your answer.
For numerical analysis, include exact numbers where possible.
If the user asks about fraud or risk, focus on transactions with label_for_fraud=1.
If you need to refer to specific transactions, use their transaction IDs.
"""
            
            # Generate content using Gemini
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                ),
            ]
            
            generate_content_config = types.GenerateContentConfig(
                temperature=0.2,  # Lower temperature for more factual responses
                top_p=0.95,
                top_k=40,
                max_output_tokens=2048,
                response_mime_type="text/plain",
            )
            
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=generate_content_config,
                )
                
                # Extract text from response
                return response.text
            except Exception as e:
                print(f"Error generating response: {e}")
                # If API call fails, try fallback
                return self._generate_fallback_response(query, transactions_data, customer_id)
        except Exception as e:
            print(f"Unexpected error in generate_response: {e}")
            return self._generate_fallback_response(query, transactions_data, customer_id)
    
    def _generate_fallback_response(self, query, transactions_data, customer_id):
        """Generate a simple fallback response without using the API."""
        try:
            query_lower = query.lower()
            total_count = len(transactions_data)
            fraud_count = sum(1 for t in transactions_data if t.get('label_for_fraud') == 1)
            fraud_percentage = (fraud_count / total_count * 100) if total_count > 0 else 0
            
            # Calculate total amount and average transaction amount
            total_amount = sum(float(t.get('transaction_amount', 0)) for t in transactions_data)
            avg_amount = total_amount / total_count if total_count > 0 else 0
            
            # Get transaction methods distribution
            methods = {}
            for t in transactions_data:
                method = t.get('method_of_transaction', 'Unknown')
                methods[method] = methods.get(method, 0) + 1
            
            # Find most common method
            most_common_method = max(methods.items(), key=lambda x: x[1])[0] if methods else "Unknown"
            
            # Generic responses
            generic_responses = [
                f"Based on your transaction data, you have {total_count} transactions, with {fraud_count} flagged as potential fraud.",
                f"Your account shows {fraud_count} suspicious transactions out of {total_count} total transactions.",
                f"You have a total of {total_count} transactions, with approximately {fraud_percentage:.1f}% flagged as potential fraud.",
                f"The total amount across all your transactions is {total_amount:.2f}.",
                f"Your most frequently used transaction method is {most_common_method}."
            ]
            
            # Query-specific responses
            if "fraud" in query_lower or "suspicious" in query_lower:
                return f"I found {fraud_count} transactions flagged as potential fraud, representing {fraud_percentage:.1f}% of your total transactions."
            
            elif "total" in query_lower and "amount" in query_lower:
                return f"The total amount across all your transactions is {total_amount:.2f}."
            
            elif "average" in query_lower:
                return f"The average transaction amount is {avg_amount:.2f}."
            
            elif "method" in query_lower or "payment" in query_lower:
                methods_str = ", ".join(f"{method}: {count}" for method, count in methods.items())
                return f"Your transaction methods breakdown: {methods_str}. The most common method is {most_common_method}."
            
            elif "help" in query_lower or "can you" in query_lower:
                return "I can help you analyze your transaction data, including fraud detection, transaction methods, amounts, and patterns. What would you like to know?"
            
            else:
                # Return a generic response if no specific patterns matched
                return random.choice(generic_responses)
                
        except Exception as e:
            print(f"Error in fallback response: {e}")
            return "I'm sorry, I'm having trouble analyzing your transaction data right now. Please try a simpler query or try again later."
    
    def _create_transactions_summary(self, transactions):
        """
        Create a summary of transactions to include in the prompt.
        
        Args:
            transactions (list): List of transaction dictionaries
            
        Returns:
            str: A text summary of the transactions
        """
        try:
            # Check if transactions is empty
            if not transactions:
                return "No transaction data available for this customer."
                
            # Count total transactions
            total_count = len(transactions)
            
            # Count fraud transactions
            fraud_count = sum(1 for t in transactions if t.get('label_for_fraud') == 1)
            
            # Calculate total transaction amount
            total_amount = sum(float(t.get('transaction_amount', 0)) for t in transactions)
            
            # Get transaction methods distribution
            methods = {}
            for t in transactions:
                method = t.get('method_of_transaction', 'Unknown')
                methods[method] = methods.get(method, 0) + 1
            
            # Get locations distribution
            locations = {}
            for t in transactions:
                location = t.get('location_data', 'Unknown')
                locations[location] = locations.get(location, 0) + 1
            
            # Format summary
            summary = f"""Total Transactions: {total_count}
Fraud Transactions: {fraud_count}
Total Transaction Amount: {total_amount:.2f}

Transaction Methods:
{self._format_dict(methods)}

Transaction Locations:
{self._format_dict(locations)}

Sample Transactions (up to 5):
{json.dumps(transactions[:5], indent=2)}
"""
            return summary
        except Exception as e:
            print(f"Error creating transaction summary: {e}")
            return f"Error summarizing transactions: {str(e)}"
    
    def _format_dict(self, d):
        """Format a dictionary as a string with each key-value pair on a new line."""
        return '\n'.join(f"- {k}: {v}" for k, v in d.items()) 