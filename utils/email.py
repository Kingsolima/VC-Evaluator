# utils/email.py
import smtplib
from email.message import EmailMessage
import os

def send_email(sender_email: str, app_password: str, recipient_email: str, body_text: str, pdf_path: str):
    msg = EmailMessage()
    msg['Subject'] = "VC Deal Memo Submission"
    msg['From'] = sender_email
    msg['To'] = recipient_email

    msg.set_content(body_text)

    # Attach the PDF file
    with open(pdf_path, 'rb') as f:
        file_data = f.read()
        file_name = os.path.basename(pdf_path)
        msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

    # Send the email using Gmail SMTP
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender_email, app_password)
        smtp.send_message(msg)

    return True
