from pydantic import BaseModel

class StartupInfo(BaseModel):
    name: str
    website: str
    round: str
    investors: str
    traction: str
    team: str
    product: str
    email_to: str

import time
from openai import OpenAI
from utils.config import (
    OPENAI_API_KEY, OPENAI_ASSISTANT_ID, GOOGLE_TOKEN_PATH,
    GMAIL_SENDER, SPREADSHEET_ID, SHEET_RANGE
)
from utils.pdf import generate_pdf_from_text
from utils.email import send_email_oauth
from utils.sheet import append_row_oauth

client = OpenAI(api_key=OPENAI_API_KEY)

def build_memo_with_assistant(prompt: str) -> str:
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=prompt)
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=OPENAI_ASSISTANT_ID)
    while True:
        r = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if r.status == "completed":
            break
        time.sleep(1)
    msgs = client.beta.threads.messages.list(thread_id=thread.id)
    for m in msgs.data:
        if m.role == "assistant":
            return m.content[0].text.value
    return ""

def process_deal(name, email_to, prompt):
    full = build_memo_with_assistant(prompt)
    email_text = full  # or split if your assistant formats sections
    pdf_path = f"output/{name}_DealMemo.pdf"
    generate_pdf_from_text(full, pdf_path)

    # Always send to both GPs
    gp_recipients = ["solimama@gmail.com", "felicia.parker@gmail.com"]  # or comma string
    send_email_oauth(
        token_path=GOOGLE_TOKEN_PATH,
        sender=GMAIL_SENDER,
        to=gp_recipients,
        subject=f"VC Deal Memo: {name}",
        body_text=email_text,
        attachment_path=pdf_path
    )


    append_row_oauth(
        token_path=GOOGLE_TOKEN_PATH,
        spreadsheet_id=SPREADSHEET_ID,
        range_name=SHEET_RANGE,
        values=[name, "emailed", "logged"]
    )
    return {"ok": True, "pdf": pdf_path}

async def submit(info: StartupInfo):
    prompt = f"""Startup: {info.name}
Website: {info.website}
Stage: {info.round}
Investors: {info.investors}
Traction: {info.traction}
Team: {info.team}
Product: {info.product}
"""
    return process_deal(name=info.name, email_to=info.email_to, prompt=prompt)
