import os, base64
from typing import List, Union, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def _load_creds(token_path: str | None):
    blob = os.getenv("GOOGLE_OAUTH_TOKEN_JSON")
    if blob:
        print("GMAIL TOKEN SOURCE=ENV", flush=True)
        return Credentials.from_authorized_user_info(json.loads(blob), SCOPES)
    if token_path and os.path.exists(token_path):
        print(f"GMAIL TOKEN SOURCE=FILE {token_path}", flush=True)
        return Credentials.from_authorized_user_file(token_path, SCOPES)
    raise RuntimeError("No Gmail token found. Set GOOGLE_OAUTH_TOKEN_JSON or provide a token file.")


def _to_list(v: Union[str, List[str], None]) -> List[str]:
    if not v:
        return []
    if isinstance(v, str):
        # allow "a@x.com, b@x.com" or "a@x.com"
        return [s.strip() for s in v.split(",") if s.strip()]
    return v

def send_email_oauth(
    token_path: str,
    sender: str,
    to: Union[str, List[str]],
    subject: str,
    mini_memo: str,
    attachment_path: Optional[str] = None,
    cc: Union[str, List[str], None] = None,
    bcc: Union[str, List[str], None] = None,
) -> str:
    to_list  = _to_list(to)
    cc_list  = _to_list(cc)
    bcc_list = _to_list(bcc)

    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    service = build('gmail', 'v1', credentials=creds)

    msg = MIMEMultipart()
    msg['From'] = sender
    if to_list: msg['To'] = ", ".join(to_list)
    if cc_list: msg['Cc'] = ", ".join(cc_list)
    msg['Subject'] = subject

    # Mini memo as HTML inside email
    html = f"""
    <html>
    <body style="font-family: monospace; white-space: pre-wrap;">
        {mini_memo.replace('\n', '<br>')}
        <br><br>
        📎 Full PDF memo attached.<br>
        <br>
        Best,<br>
        VC Evaluator GPT
    </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))


    if attachment_path:
        with open(attachment_path, 'rb') as f:
            part = MIMEApplication(f.read(), _subtype='pdf')
            part.add_header('Content-Disposition', 'attachment',
                            filename=os.path.basename(attachment_path))
            msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    sent = service.users().messages().send(userId='me', body={'raw': raw}).execute()
    return sent.get('id', '')
