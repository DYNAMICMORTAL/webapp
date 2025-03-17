# UBIShield Banking Application

## Transaction Network Visualization and Chat Interface

This application includes a powerful transaction network visualization and chat interface for analyzing customer transaction data.

## Features

- **Transaction Visualization**: Interactive graph visualization of customer transaction networks
- **Filtering Options**: Filter visualization by fraud, genuine transactions, or search for specific counterparties
- **Chat Interface**: AI-powered chat interface to query transaction data using natural language

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy the `.env.example` file to `.env`: 
   ```
   cp .env.example .env
   ```
4. Set up your Gemini API key in the `.env` file:
   ```
   GEMINI_API_KEY=your-gemini-api-key-here
   ```
5. Run the Django server: `python manage.py runserver`
6. Access the application at: http://localhost:8000/

## Using the Chat Interface

The chat interface allows you to ask questions about transaction data in natural language, such as:

- "Show me all suspicious transactions in the last month"
- "Which transaction methods have the highest fraud rate?"
- "Analyze patterns in my flagged transactions"
- "What's the total amount of fraud transactions?"
- "Which locations have the most transactions?"

## Getting a Gemini API Key

1. Go to the [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key
5. Add it to your `.env` file as `GEMINI_API_KEY=your-key-here`

## Dependencies

- Django
- pandas
- google-generativeai
- python-dotenv
- vis.js (included via CDN)

## Troubleshooting

### Chat Interface Not Working

If you receive a 500 (Internal Server Error) when using the chat interface:

1. **Check API Key**: Make sure you've added your Gemini API key to the `.env` file
2. **Check Console**: Look for any JavaScript errors in the browser console
3. **Check Server Logs**: Look for errors in the Django server console output

### Model Not Available

The application tries to use the following models in order:
1. `gemini-2.0-pro-exp-02-05`
2. `gemini-1.5-pro`
3. `gemini-1.0-pro`

If none of these models are available with your API key, you'll need to modify the model name in `transaction_chat.py` to use a model that your API key has access to.

### CSV Data Issues

Make sure the transaction CSV data file exists at `bankapp/branches/data/final_synthetic_transactions.csv`. If it's located elsewhere, update the path in `views.py`. 