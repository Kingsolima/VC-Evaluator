from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time
from openai import OpenAI
import re
from utils.config import (
    OPENAI_API_KEY, OPENAI_ASSISTANT_ID, GOOGLE_TOKEN_PATH,
    GMAIL_SENDER, SPREADSHEET_ID, SHEET_RANGE,
    # optional: read recipients from .env (comma-separated)
    # e.g., GP_RECIPIENTS=gp1@vc.com, gp2@vc.com
    GP_RECIPIENTS,
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

    # Pull all fields
    first_name  = extra.get("first_name", "")
    last_name   = extra.get("last_name", "")
    founder_em  = extra.get("founder_email", "")
    incorp      = extra.get("incorporation", "")
    position    = extra.get("position", "")
    problem     = extra.get("problem", "")
    solution    = extra.get("solution", "")
    market      = extra.get("market", "")
    team_detail = extra.get("team_detail", "") or info.team
    university  = extra.get("university", "")
    competition = extra.get("competition", "")
    milestones  = extra.get("milestones", "")
    vision      = extra.get("vision", "")
    business_model = extra.get("business_model", "")
    traction_detail = extra.get("traction_detail", "") or info.traction
    cap_table = extra.get("cap_table", "")
    press_links = extra.get("press_links", "")
    round_size = extra.get("round_size", "")
    industry = extra.get("industry", "")

    return f"""
You are a venture capital associate writing two outputs:

First, a **mini deal memo email** using the real company info below. Then, a full investor memo for PDF.

---

### MINI DEAL MEMO EMAIL

Hi GP,

Here is a full mini memo for {info.name}, {info.product}. They are currently raising a {info.round} round, with notable interest from {info.investors}.

🏷️ **Startup Overview**
- **Name**: {info.name}
- **Website**: {info.website}
- **Industry**: {industry}
- **Round Stage**: {info.round}
- **Round Size**: {round_size}
- **Investors**: {info.investors}

📈 **Market**
{market}

🔍 **Problem**
{problem}

🛠 **Solution**
{solution}

📊 **Traction**
{traction_detail}

💵 **Business Model**
{business_model}

🧱 **Moat / Defensibility**
{extra.get("moat", "")}

👥 **Team**
{team_detail}

🚩 **Red Flags / Risks**
{extra.get("risks", "")}

🧪 **Product Stage**
{extra.get("product_stage", "")}

📊 📊 **Scorecard (computed)**
Compute scores using this rubric (max points):
- Team 0–25
- Market 0–20
- Product 0–10
- Vision 0–5
- Traction 0–10
- Business Model 0–5
- Moat 0–25
- Risk Adjustment 0 to -10 (if their isnt much risk dont adjust much, like 10 is for extreme cases)
- Bonus 0…+5

Rules:
- Total = sum(all above) bounded to 0…100.
- Verdict mapping:
  - total ≥ 80 → "TAKE_CALL"
  - 70–79 → "LEARN_MORE"
  - 50-70 → "PASS"

After the email text, output a single JSON block **exactly** like this, fenced in triple backticks:

```json
{{"scores": {{"team": 0, "market": 0, "product": 0, "vision": 0, "traction": 0, "business_model": 0, "moat": 0, "risk_adj": 0, "bonus": 0}}, "total": 0, "verdict": "LEARN_MORE"}}
📎 Full PDF memo attached.

Best,  
VC Evaluator GPT

---

### FULL DEAL MEMO

Now write a long-form PDF memo using the same info in the style of Replit's Series C investment memo.

Structure:
- We are excited to invest...
- Why we're excited...
- **Synopsis**
- **Problem**
- **Solution**
- **Business Model**
- **Market Size**
- **Go to Market Strategy**
- **Traction**
- **Competitors**
- **The Team**
- **The Cap Table**
- **Exit Strategy**
- **Press**

Use bold headers, markdown formatting, and professional tone. Include data.
"""

def parse_scorecard_json(text: str) -> Optional[Dict[str, Any]]:
    # look for the last fenced JSON block
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if not m:
        # fallback: any fenced block
        m = re.search(r"```\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not m:
        return None
    import json
    try:
        return json.loads(m.group(1))
    except Exception:
        return None

def extract_score(mini_text: str, full_text: str | None = None) -> str:
    # try JSON in mini, then full
    sc = parse_scorecard_json(mini_text)
    if not sc and full_text:
        sc = parse_scorecard_json(full_text)

    if sc is not None:
        total = sc.get("total")
        try:
            total = float(str(total).strip())
        except (TypeError, ValueError):
            total = None
        if total is not None:
            total = max(0.0, min(100.0, total))  # clamp
            return str(int(round(total)))

    # fallback to prose pattern: "Total: 82" or "Total: 82/100"
    pat = re.compile(r"Total:\s*(\d+)(?:\s*/\s*100)?", re.IGNORECASE)
    m = pat.search(mini_text) or (pat.search(full_text) if full_text else None)
    return m.group(1) if m else "N/A"


def extract_action(text: str) -> str:
    sc = parse_scorecard_json(text)
    if sc and isinstance(sc.get("verdict"), str):
        v = sc["verdict"].upper().replace(" ", "_")
        mapping = {
            "TAKE_CALL": "📞 Take a Call",
            "LEARN_MORE": "⚖️ Learn More",
            "PASS": "❌ Pass",
            "HARD_PASS": "❌ Pass",  # in case the model outputs it
        }
        return mapping.get(v, "N/A")
    for phrase in ["📞 Take a Call", "⚖️ Learn More", "❌ Pass"]:
        if phrase in text:
            return phrase
    return "N/A"


def extract_field(label: str, text: str) -> str:
    """
    Grab the block of text that comes after a section header whose visible
    label matches `label` (e.g., "Traction", "Team"), ignoring emojis and **bold**.
    Works across multiple lines until the next header.
    """
    # All possible section titles that can follow
    next_headers = (
        r"Startup Overview|Market|Problem|Solution|Traction|Business Model|"
        r"Moat / Defensibility|Moat|Team|Red Flags / Risks|Product Stage|Scorecard"
    )

    # ^ start of line; optional emoji; optional spaces; optional **; label; optional **; end of line
    header = rf"^\s*(?:[🏷️📈🔍🛠📊💵🧱👥🚩🧪]\s*)?\**{re.escape(label)}\**\s*$"

    # Capture everything after that header until the next header or end of text
    pattern = rf"(?ims){header}\n+(.*?)(?=^\s*(?:[🏷️📈🔍🛠📊💵🧱👥🚩🧪]\s*)?\**(?:{next_headers})\**\s*$|\Z)"
    m = re.search(pattern, text)
    return m.group(1).strip() if m else "Unknown"


def extract_revenue(traction_text: str) -> str:
    patterns = [
        r"\$[0-9][0-9,\.]*\s*[kKmM]?\s*(?:ARR|MRR|annual|monthly)?",  # $450K ARR, $20k MRR, $1.2M
        r"[0-9][0-9,\.]*\s*(?:users|customers|clients)\b",            # 6 customers (proxy)
        r"\b[0-9]+\s*(?:paying customers|subs|subscriptions)\b"
    ]
    for p in patterns:
        m = re.search(p, traction_text, re.IGNORECASE)
        if m:
            return m.group(0)
    return "Unknown"


def extract_reason(full_memo: str, summary: str) -> str:
    m = re.search(r"Why we'?re excited[:\-]?\s*(.*?)(?:\n\n|\Z)", full_memo,
                  re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()

    # Fallback: pull top 1–2 bullets from Traction or Moat
    for sec in ("Traction", "Moat / Defensibility", "Market"):
        block = extract_field(sec, full_memo)
        if block and block != "Unknown":
            lines = [ln.strip("-• ").strip() for ln in block.splitlines() if ln.strip()]
            if lines:
                return "; ".join(lines[:2])
    return summary[:200]  # last-ditch: a concise summary

def extract_summary(text: str) -> str:
    # Capture between "Hi GP," and the first header (with or without emoji/bold)
    headers = (
        r"Startup Overview|Market|Problem|Solution|Traction|Business Model|"
        r"Moat / Defensibility|Moat|Team|Red Flags|Product Stage|Scorecard|FULL DEAL MEMO"
    )
    pat = rf"(?is)Hi GP,?\s*(.*?)(?=\n\s*(?:[^\w\s]?\s*)?\**(?:{headers})\**\b)"
    m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
    if m:
        s = m.group(1).strip()
        if s:
            return s
    return ""




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

    # Send email
    # Prefer explicit GP recipients from env; do NOT email founder by default
    gp_list = [e.strip() for e in (GP_RECIPIENTS or "").split(",") if e.strip()]
    recipients = gp_list  # if empty, nothing is sent; that’s safer than emailing founder

    send_email_oauth(
        token_path=GOOGLE_TOKEN_PATH,
        sender=GMAIL_SENDER,
        to=recipients,
        subject=f"Deal Memo – {name} ({info_round_from_prompt(prompt)})",
        mini_memo=mini_memo,
        attachment_path=pdf_path
    )

    # Extract data and log to Google Sheets

    
    summary = extract_summary(mini_memo)
    if not summary:
        # Build a sane one-liner fallback from structured fields
        summary = f"{name} is building {extract_field('Solution', mini_memo) or 'an AI product'}; " \
                f"stage: {info_round_from_prompt(prompt)}; " \
                f"traction: {extract_field('Traction', mini_memo)}; " \
                f"backed by {extract_field('Startup Overview', mini_memo) or 'notable investors'}."


    traction = extract_field("Traction", mini_memo)
    team = extract_field("Team", mini_memo)


    revenue = extract_revenue(traction)

    tags = "AI SaaS, Automation"
    scorecard = extract_score(mini_memo, full_memo) or {}
    total = scorecard.get("total")
    verdict = scorecard.get("verdict", "")
    score = str(int(round(total))) if isinstance(total, (int, float)) else "N/A"

    # Keep your existing extract_action as fallback, but prefer JSON:
    if isinstance(verdict, str) and verdict:
        v = verdict.upper().replace(" ", "_")
        action = {"TAKE_CALL":"📞 Take a Call","LEARN_MORE":"⚖️ Learn More","PASS":"❌ Pass"}.get(v, "⚖️ Learn More")
    else:
        action = extract_action(mini_memo)  # legacy fallback    action = extract_action(mini_memo)
        reason = extract_reason(full_memo, summary)

    csv_row = [
        name,
        summary,
        traction,
        revenue,
        team,
        info_round_from_prompt(prompt),
        tags,
        score,
        "Mini memo sent",
        action,
        reason
    ]


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
