import os
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY      = os.getenv('OPENAI_API_KEY', '')
OPENAI_ASSISTANT_ID = os.getenv('OPENAI_ASSISTANT_ID', '')

GOOGLE_TOKEN_PATH   = os.getenv('GOOGLE_TOKEN_PATH', 'token.json')
GMAIL_SENDER        = os.getenv('GMAIL_SENDER', '')

SPREADSHEET_ID      = os.getenv('SPREADSHEET_ID', '')
SHEET_RANGE         = os.getenv('SHEET_RANGE', 'Sheet1!A1')
