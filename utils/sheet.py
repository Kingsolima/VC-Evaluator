# utils/sheet.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Make sure you create and download your service account key JSON file
# and place the path to it below
GOOGLE_CREDS_PATH = "credentials/google_creds.json"

GOOGLE_SHEET_ID = ""  # <-- Add your actual Sheet ID here


def update_google_sheet(info, memo_summary):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_PATH, scope)
    client = gspread.authorize(creds)

    # Open the sheet by ID
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1

    row = [
        datetime.utcnow().isoformat(),
        info.name,
        info.website,
        info.round,
        info.investors,
        info.traction,
        info.team,
        info.product,
        memo_summary.strip().replace("\n", " ")[:500]  # limit to 500 characters
    ]

    sheet.append_row(row)
    return True
