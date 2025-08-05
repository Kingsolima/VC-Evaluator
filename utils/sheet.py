from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def append_row_oauth(token_path, spreadsheet_id, range_name, values):
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    body = {'values': [values]}
    return service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body=body
    ).execute()
