import os, base64
from typing import List, Union, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

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
    body_text: str,
    attachment_path: Optional[str] = None,
    cc: Union[str, List[str], None] = None,
    bcc: Union[str, List[str], None] = None,
) -> str:
    """Send via Gmail API; 'to', 'cc', 'bcc' accept str or list."""
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
    msg.attach(MIMEText(body_text, 'plain'))

    if attachment_path:
        with open(attachment_path, 'rb') as f:
            part = MIMEApplication(f.read(), _subtype='pdf')
            part.add_header('Content-Disposition', 'attachment',
                            filename=os.path.basename(attachment_path))
            msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    sent = service.users().messages().send(userId='me', body={'raw': raw}).execute()
    return sent.get('id', '')
