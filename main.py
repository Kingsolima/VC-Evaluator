# vc_tool/main.py

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import openai
import os
import time
from utils.pdf import generate_pdf_from_text
from utils.email import send_email
from utils.sheet import update_google_sheet
from utils.webhook import router as webhook_router

app = FastAPI()
app.include_router(webhook_router)

# === SET YOUR API KEYS ===
openai.api_key = ""  # <- PUT YOUR OPENAI API KEY HERE
GOOGLE_SHEET_ID = ""  # <- PUT YOUR GOOGLE SHEET ID HERE
GMAIL_SENDER = ""      # <- YOUR EMAIL (e.g., vc@example.com)
GMAIL_APP_PASSWORD = ""  # <- Gmail App Password (not your main password)

ASSISTANT_ID = ""  # <- YOUR OpenAI Assistant ID with Retrieval + Instructions set

class StartupInfo(BaseModel):
    name: str
    website: str
    round: str
    investors: str
    traction: str
    team: str
    product: str
    email_to: str

@app.post("/submit")
async def submit(info: StartupInfo):
    # Create a thread
    thread = openai.beta.threads.create()

    # Format message
    user_prompt = f"""
Startup: {info.name}
Website: {info.website}
Stage: {info.round}
Investors: {info.investors}
Traction: {info.traction}
Team: {info.team}
Product: {info.product}
"""
    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_prompt
    )

    # Run the assistant
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    while True:
        status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if status.status == "completed":
            break
        time.sleep(1)

    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    full_response = messages.data[0].content[0].text.value

    # Split summary vs full memo
    if "### FULL DEAL MEMO" in full_response:
        email_text, full_memo = full_response.split("### FULL DEAL MEMO")
    else:
        email_text = full_response
        full_memo = "Memo not properly separated. Review Assistant output."

    # Save text and generate PDF
    pdf_path = f"output/{info.name}_DealMemo.pdf"
    generate_pdf_from_text(full_memo, pdf_path)

    # Send email
    send_email(GMAIL_SENDER, GMAIL_APP_PASSWORD, info.email_to, email_text, pdf_path)

    # Update sheet
    update_google_sheet(info, email_text)

    return {"status": "Memo created and sent", "pdf": pdf_path}
