import os
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY      = os.getenv('OPENAI_API_KEY', '')
OPENAI_ASSISTANT_ID = os.getenv('OPENAI_ASSISTANT_ID', '')

GOOGLE_TOKEN_PATH   = os.getenv('GOOGLE_TOKEN_PATH', 'token.json')
GMAIL_SENDER        = os.getenv('GMAIL_SENDER', '')

SPREADSHEET_ID      = os.getenv('SPREADSHEET_ID', '')
SHEET_RANGE         = os.getenv('SHEET_RANGE', 'Sheet1!A1')

GP_RECIPIENTS = os.getenv('GP_RECIPIENTS', '') 

import json, tempfile

GOOGLE_TOKEN_JSON = os.getenv("GOOGLE_TOKEN_JSON", "")
if GOOGLE_TOKEN_JSON:
    try:
        info = json.loads(GOOGLE_TOKEN_JSON)
        tmp = tempfile.NamedTemporaryFile(prefix="google_token_", suffix=".json", delete=False)
        tmp.write(json.dumps(info).encode("utf-8"))
        tmp.flush()
        # this is what email.py & sheet.py use
        GOOGLE_TOKEN_PATH = tmp.name
    except Exception:
        pass

