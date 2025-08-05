import openai
import os
import time
from pydantic import BaseModel
from utils.pdf import generate_pdf_from_text
from utils.email import send_email
from utils.sheet import update_google_sheet
from api import openai_key

# Use environment variables or set manually for now
ASSISTANT_ID = ""  # Put your Assistant ID here
GMAIL_SENDER = ""  # Your Gmail
GMAIL_APP_PASSWORD = ""  # Your Gmail App Password

class StartupInfo(BaseModel):
    name: str
    website: str
    round: str
    investors: str
    traction: str
    team: str
    product: str
    email_to: str

async def submit(info: StartupInfo):
    # Create a thread for OpenAI Assistant
    thread = openai.beta.threads.create()

    # Format user message
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

    # Poll until assistant finishes
    while True:
        status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if status.status == "completed":
            break
        time.sleep(1)

    # Get the response
    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    full_response = messages.data[0].content[0].text.value

    # Separate email summary from full memo
    if "### FULL DEAL MEMO" in full_response:
        email_text, full_memo = full_response.split("### FULL DEAL MEMO")
    else:
        email_text = full_response
        full_memo = "Memo not properly separated. Review Assistant output."

    # Create PDF
    pdf_path = f"output/{info.name}_DealMemo.pdf"
    generate_pdf_from_text(full_memo, pdf_path)

    # Send email
    send_email(GMAIL_SENDER, GMAIL_APP_PASSWORD, info.email_to, email_text, pdf_path)

    # Update Google Sheet
    update_google_sheet(info, email_text)

    return {"status": "Memo created and sent", "pdf": pdf_path}
