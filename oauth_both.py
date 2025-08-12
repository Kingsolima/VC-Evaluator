from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/spreadsheets',
]

flow = InstalledAppFlow.from_client_secrets_file('credentials_desktop.json', SCOPES)
# Fixed port helps on Windows; also forces refresh_token:
creds = flow.run_local_server(host='localhost', port=8080, access_type='offline', prompt='consent')

open('token.json', 'w').write(creds.to_json())
print('✅ token.json written')
