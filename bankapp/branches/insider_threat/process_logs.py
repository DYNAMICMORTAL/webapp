import json
import os
import base64
from google import genai
from google.genai import types
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

def load_logs_from_directory(logs_dir):
    """Load all JSON log files from the specified directory."""
    logs_data = {}
    logs_path = Path(logs_dir)
    
    # Print the directory being searched for debugging
    print(f"Looking for log files in: {logs_path.absolute()}")
    
    if not logs_path.exists():
        print(f"Directory not found: {logs_path.absolute()}")
        return logs_data
    
    # List all files in the directory for debugging
    print(f"Files in directory: {[f.name for f in logs_path.glob('*')]}")
    
    for file_path in logs_path.glob("*.json"):
        try:
            print(f"Loading file: {file_path}")
            with open(file_path, 'r') as file:
                file_data = json.load(file)
                logs_data[file_path.stem] = file_data
                print(f"Successfully loaded {file_path.stem} with {len(file_data)} entries")
        except json.JSONDecodeError as e:
            print(f"JSON parsing error in {file_path}: {e}")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    return logs_data

def prepare_prompt_for_gemini(logs_data):
    """Prepare the input prompt for Gemini with the logs data."""
    insider_threats = logs_data.get('insider_threat_logs', [])
    activity_logs = logs_data.get('activity_logs', [])
    
    prompt = """
You are a security analyst specialized in insider threat detection. 
Review the following logs and identify potential insider threats.

IMPORTANT: You MUST generate 'severity', 'risk_score', 'analysis' and 'recommended_actions' fields for EACH alert.

IMPORTANT: Return your response as a JSON array of alert objects directly, not wrapped in any outer object.
For example, return: [{"alert_id": "A123456", ...}, {...}]

For each suspicious activity, provide a detailed analysis with the following fields:
- alert_id (original ID from logs)
- employee (object with name, department, initials)
- activity (object with type, description, time, location, details)
- severity (Critical/High/Medium/Low)
- status (keep original from logs)
- risk_score (0-100)
- analysis (detailed explanation of the threat)
- recommended_actions (array of 2-4 specific actions)

For the severity field, use these guidelines:
- Critical: Immediate threat requiring urgent intervention
- High: Significant threat requiring rapid response
- Medium: Moderate threat requiring investigation
- Low: Minor issue that should be monitored

For the risk_score field, use a scale of 0-100:
- 90-100: Critical threats with immediate danger
- 70-89: High-risk threats
- 40-69: Medium-risk threats
- 0-39: Low-risk threats

Focus on unusual activities such as:
1. Unauthorized access attempts
2. Access outside normal working hours
3. Unusual data transfers or downloads
4. Privilege escalation attempts
5. Configuration changes without approval
6. Access to sensitive information without proper authorization

LOGS DATA:

## Insider Threat Alerts:
"""
    
    prompt += json.dumps(insider_threats, indent=2)
    
    prompt += """

## Detailed Activity Logs:
"""
    
    prompt += json.dumps(activity_logs, indent=2)
    
    return prompt

def call_gemini_llm(prompt):
    """Call Gemini LLM with the prepared prompt."""
    client = genai.Client(
        api_key=os.environ.get("GOOGLE_API_KEY"),
    )

    model = "gemini-2.0-pro-exp-02-05"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=0.2,  # Lower temperature for more focused responses
        top_p=0.95,
        top_k=64,
        max_output_tokens=8192,
        response_mime_type="application/json",  # Request JSON response
    )

    response_text = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        chunk_text = chunk.text
        print(chunk_text, end="")
        response_text += chunk_text
    
    return response_text

def save_response(response, output_file):
    """Save the LLM response to a file."""
    with open(output_file, 'w') as file:
        file.write(response)
    print(f"\nResponse saved to {output_file}")

def main():
    # Set up paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(current_dir, "logs")
    output_file = os.path.join(current_dir, "insider_threat_analysis.json")
    
    
    print(f"Loading logs from {logs_dir}...")
    logs_data = load_logs_from_directory(logs_dir)
    
    if not logs_data:
        print("No log files found or all files failed to load.")
        return
    
    print(f"Found {len(logs_data)} log files.")
    
    print("Preparing prompt for Gemini LLM...")
    prompt = prepare_prompt_for_gemini(logs_data)
    
    print("Calling Gemini LLM for analysis...")
    response = call_gemini_llm(prompt)
    
    print("Saving response...")
    save_response(response, output_file)
    
    print("Done!")

if __name__ == "__main__":
    main() 