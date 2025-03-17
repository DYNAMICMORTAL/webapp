import os
import base64
import json
from pathlib import Path
from mistralai import Mistral, ImageURLChunk, TextChunk
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class KYCAgent:
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.client = Mistral(api_key=self.api_key)
        
    def process_document(self, image_path):
        """Process a KYC document using Mistral OCR"""
        # Validate input file
        image_file = Path(image_path)
        if not image_file.is_file():
            raise FileNotFoundError(f"The provided image path does not exist: {image_path}")

        # Read and encode the image file
        encoded_image = base64.b64encode(image_file.read_bytes()).decode()
        base64_data_url = f"data:image/jpeg;base64,{encoded_image}"

        # Process the image using OCR
        print(f"\nProcessing document: {image_path}")
        image_response = self.client.ocr.process(
            document=ImageURLChunk(image_url=base64_data_url),
            model="mistral-ocr-latest"
        )
        
        if not image_response.pages:
            print("No OCR results found")
            return {"error": "No OCR results found"}
            
        image_ocr_markdown = image_response.pages[0].markdown
        
        # Print OCR results for debugging
        print("\n--- OCR RESULTS ---")
        print(image_ocr_markdown)
        print("--- END OCR RESULTS ---\n")

        # Parse the OCR result into a structured JSON response
        chat_response = self.client.chat.complete(
            model="pixtral-12b-latest",
            messages=[
                {
                    "role": "user",
                    "content": [
                        ImageURLChunk(image_url=base64_data_url),
                        TextChunk(text=(
                            f"This is the image's OCR in markdown:\n{image_ocr_markdown}\n.\n"
                            "Extract all relevant KYC information from this document. "
                            "If this is an Aadhaar card, extract the Aadhaar number, name, date of birth, gender, and address. "
                            "If this is a PAN card, extract the PAN number, name, father's name, and date of birth. "
                            "Return the data in a structured JSON format."
                            )
                        )
                    ]
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        result = json.loads(chat_response.choices[0].message.content)
        print(f"Extracted data: {json.dumps(result, indent=2)}")
        return result
    
    def process_onboarding_data(self, file_path):
        """Process customer onboarding data from a text file"""
        # Validate input file
        file_path = Path(file_path)
        if not file_path.is_file():
            return {"error": f"Onboarding data file not found: {file_path}"}
        
        # Read the onboarding data file
        with open(file_path, 'r') as f:
            onboarding_text = f.read()
        
        print(f"\nProcessing onboarding data: {file_path}")
        
        # Use Mistral to parse the onboarding data into structured format
        chat_response = self.client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {
                    "role": "user",
                    "content": [
                        TextChunk(text=(
                            f"Here is customer onboarding data in text format:\n\n{onboarding_text}\n\n"
                            "Parse this data into a structured JSON format with appropriate fields and values. "
                            "Include all relevant customer information such as personal details, address, "
                            "employment information, banking details, and any risk-related information."
                        ))
                    ]
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        result = json.loads(chat_response.choices[0].message.content)
        print(f"Extracted onboarding data: {json.dumps(result, indent=2)}")
        return result
    
    def analyze_customer_profile(self, customer_id):
        """Analyze a customer's KYC documents and create a risk profile"""
        try:
            kyc_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "kycdata", str(customer_id))
            if not os.path.exists(kyc_dir):
                print(f"No KYC data found for customer {customer_id}, using synthetic data")
                return self._generate_mock_profile_assessment(customer_id)
            
            kyc_data = {}
            
            # Process onboarding data if available
            onboarding_file = os.path.join(kyc_dir, "customer_onboarding.txt")
            if os.path.exists(onboarding_file):
                try:
                    kyc_data["onboarding"] = self.process_onboarding_data(onboarding_file)
                except Exception as e:
                    print(f"Error processing onboarding data: {str(e)}")
                    kyc_data["onboarding"] = {"error": str(e)}
            
            # Process all document images in the customer's KYC directory
            for doc_file in os.listdir(kyc_dir):
                doc_path = os.path.join(kyc_dir, doc_file)
                if doc_file.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')) and doc_file != "customer_onboarding.txt":
                    doc_type = "aadhar" if "aadhar" in doc_file.lower() else "pan"
                    try:
                        kyc_data[doc_type] = self.process_document(doc_path)
                    except Exception as e:
                        print(f"Error processing {doc_type} document: {str(e)}")
                        kyc_data[doc_type] = {"error": str(e)}
            
            # Use LLM to assess profile risk
            risk_assessment_prompt = """
            Analyze the following customer KYC data and provide a risk assessment based on this methodology:

            Risk Factor Analysis Methodology:

            Identity Verification (30% total)
            - Document Validity (15%): Analyze document authenticity, expiration, and consistency
            - Identity Consistency (10%): Check for consistency across name, address, and other identifiers
            - Digital Footprint (5%): Evaluate presence and history on social media, professional networks

            Financial Behavior (27% total)
            - Transaction Patterns (12%): Analyze typical transaction amounts, frequency, and types
            - Account Balance Volatility (8%): Measure stability of account balances
            - Income-Expense Ratio (7%): Evaluate relationship between income and spending

            Demographic and External Factors (28% total)
            - Geographic Risk (6%): Assess risk based on customer location
            - Occupation Risk (5%): Evaluate risk associated with profession
            - Age and Experience (3%): Consider age-related risk factors
            - Credit History (8%): Review credit score and history
            - Public Records (6%): Check for legal issues, bankruptcies, etc.

            Technical Signals (15% total)
            - Device Reputation (7%): Assess risk of device used
            - Connection Security (5%): Evaluate security of connection
            - Application Interaction (3%): Analyze how customer interacts with application

            KYC Data:
            {kyc_data}

            Provide a risk assessment with:
            1. Overall risk score (0-100)
            2. Risk category (Low, Medium, High)
            3. List of key risk factors identified
            4. Brief explanation of the assessment
            
            Return the assessment as a JSON object with fields: risk_score, risk_category, risk_factors, explanation.
            """
            
            # If Mistral API key is not available or there's an error, return mock data
            if not self.api_key:
                print("No API key available for Mistral - returning mock profile assessment")
                return self._generate_mock_profile_assessment(customer_id, kyc_data)
            
            try:
                chat_response = self.client.chat.complete(
                    model="mistral-large-latest",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                TextChunk(text=risk_assessment_prompt.format(kyc_data=json.dumps(kyc_data, indent=2)))
                            ]
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0
                )
                
                profile_risk = json.loads(chat_response.choices[0].message.content)
                print(f"\nRisk Assessment Results: {json.dumps(profile_risk, indent=2)}")
                
                return {
                    "customer_id": customer_id,
                    "kyc_data": kyc_data,
                    "profile_risk": profile_risk
                }
                
            except Exception as e:
                print(f"Error in Mistral API call: {str(e)}")
                return self._generate_mock_profile_assessment(customer_id, kyc_data)
        
        except Exception as e:
            print(f"Error analyzing customer profile: {str(e)}")
            return self._generate_mock_profile_assessment(customer_id)

    def _generate_mock_profile_assessment(self, customer_id, kyc_data=None):
        """Generate a mock profile assessment when API is unavailable"""
        if kyc_data is None:
            kyc_data = {}
        
        # Use customer_id to create a pseudo-random but consistent risk score
        import hashlib
        
        # Hash the customer_id to get a consistent number
        hash_obj = hashlib.md5(str(customer_id).encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        
        # Generate risk score between 30-75
        risk_score = 30 + (hash_int % 45)
        
        # Determine risk category
        if risk_score >= 60:
            risk_category = "Medium"
        else:
            risk_category = "Low"
        
        # Generate mock profile risk assessment
        profile_risk = {
            "risk_score": risk_score,
            "risk_category": risk_category,
            "risk_factors": [
                "Customer profile analysis based on limited data",
                "Automated risk assessment due to API limitations"
            ],
            "explanation": f"This is an automated risk assessment for customer {customer_id} based on available KYC data."
        }
        
        return {
            "customer_id": customer_id,
            "kyc_data": kyc_data,
            "profile_risk": profile_risk
        }