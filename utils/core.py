from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time
from openai import OpenAI

from utils.config import (
    OPENAI_API_KEY, OPENAI_ASSISTANT_ID, GOOGLE_TOKEN_PATH,
    GMAIL_SENDER, SPREADSHEET_ID, SHEET_RANGE,
    # optional: read recipients from .env (comma-separated)
    # e.g., GP_RECIPIENTS=gp1@vc.com, gp2@vc.com
)
from utils.pdf import generate_pdf_from_text
from utils.email import send_email_oauth
from utils.sheet import append_row_oauth

client = OpenAI(api_key=OPENAI_API_KEY)

class StartupInfo(BaseModel):
    name: str
    website: str
    round: str
    investors: str
    traction: str
    team: str
    product: str
    email_to: str  # keep for backward-compat; we can still add a 2nd GP below

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

def _build_prompt(info: StartupInfo, extra: Optional[Dict[str, Any]]) -> str:
    extra = extra or {}
    # Safely pull extras
    first_name  = extra.get("first_name", "")
    last_name   = extra.get("last_name", "")
    founder_em  = extra.get("founder_email", "")
    incorp      = extra.get("incorporation", "")
    position    = extra.get("position", "")
    problem     = extra.get("problem", "")
    solution    = extra.get("solution", "")
    market      = extra.get("market", "")
    team_detail = extra.get("team_detail", "")
    university  = extra.get("university", "")
    competition = extra.get("competition", "")
    milestones  = extra.get("milestones", "")
    vision      = extra.get("vision", "")
    # pitch deck: Typeform will send a URL; include if you have it
    pitch_deck  = extra.get("pitch_deck_url", "")

    # Clear, structured instructions for the Assistant
    return f"""
You are a VC associate writing a concise email summary (6–8 sentences) and a full investor-grade deal memo.

Start with a short **Email Summary** (for body of email).
Then insert the delimiter line exactly:
### FULL DEAL MEMO
After that, write the long-form memo.

Use the structure below. Be specific, avoid fluff.

Company: {info.name}
Website: {info.website}
Round: {info.round}
Lead/Investors: {info.investors}
Traction: {info.traction}
Team (short): {info.team}
Product (short): {info.product}

Founder First Name: {first_name}
Founder Last Name: {last_name}
Founder Email: {founder_em}
Incorporation: {incorp}
Position: {position}

Problem:
{problem}

Solution / Product:
{solution}

Market (TAM/SAM/SOM if provided):
{market}

Team (detail):
{team_detail}

University:
{university}

Competition / Differentiation:
{competition}

Milestones to Next Round:
{milestones}

Vision (5–10y, exit expectations):
{vision}

Pitch Deck URL (if available):
{pitch_deck}

Formatting rules:
- Email Summary: 6–8 sentences, neutral-professional. End with a crisp GP recommendation (e.g., "📞 Take a Call" or "⚖️ Learn More").
- After "### FULL DEAL MEMO", include sections:
  1) Overview
  2) Market
  3) Problem & Solution
  4) Traction & Business Model
  5) Moat & Defensibility
  6) Team
  7) Risks / Red Flags
  8) Competition
  9) Milestones & Use of Funds
  10) Scorecard (bullet points)
  11) GP Recommendation
- Use short paragraphs and bullets where helpful.
- Be decisive. Include numbers if mentioned.
"""

def process_deal(name: str, email_to, prompt: str):
    full_output = build_memo_with_assistant(prompt)

    if "### FULL DEAL MEMO" in full_output:
        mini_memo, full_memo = full_output.split("### FULL DEAL MEMO", 1)
    else:
        mini_memo = full_output
        full_memo = full_output

    mini_memo = mini_memo.strip()
    full_memo = full_memo.strip()

    pdf_path = f"output/{name}_DealMemo.pdf"
    generate_pdf_from_text(full_memo, pdf_path)

    recipients: List[str] = []
    if isinstance(email_to, str) and email_to.strip():
        recipients.append(email_to.strip())
    recipients.append("second.gp@yourvc.com")

    send_email_oauth(
        token_path=GOOGLE_TOKEN_PATH,
        sender=GMAIL_SENDER,
        to=recipients,
        subject=f"VC Deal Memo: {name}",
        mini_memo=mini_memo,
        attachment_path=pdf_path
    )

    csv_row = [name, info_round_from_prompt(prompt), "Mini memo sent", "Full memo attached"]
    append_row_oauth(
        token_path=GOOGLE_TOKEN_PATH,
        spreadsheet_id=SPREADSHEET_ID,
        range_name=SHEET_RANGE,
        values=csv_row
    )

    return {"ok": True, "pdf": pdf_path}


def info_round_from_prompt(prompt: str) -> str:
    # tiny helper to log round in sheet even if prompt changes
    for tag in ["Pre-Seed", "Seed", "Series A", "Series B"]:
        if tag.lower() in prompt.lower():
            return tag
    return "N/A"

async def submit(info: StartupInfo, extra_context: Optional[Dict[str, Any]] = None):
    prompt = _build_prompt(info, extra_context)
    return process_deal(name=info.name, email_to=info.email_to, prompt=prompt)
