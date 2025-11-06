# core.py - Slim orchestration only (down from 800+ lines to ~100 lines)
import time
import re
from typing import Dict, Any, Optional
from openai import OpenAI

# Import models and utilities from refactored modules
from utils.memo_schema import StartupInfo
from utils.prompt_builder import build_investment_memo_prompt
from utils.scoring_engine import parse_score_any, calibrate_scorecard, build_decision_rationale
from field_map import extract_field, extract_revenue, extract_summary, infer_tags
from utils.config import (
    OPENAI_API_KEY, OPENAI_ASSISTANT_ID, GOOGLE_TOKEN_PATH,
    GMAIL_SENDER, SPREADSHEET_ID, SHEET_RANGE, GP_RECIPIENTS,
)
from utils.pdf import generate_pdf_from_text
from utils.email import send_email_oauth
from utils.sheet import append_row_oauth

client = OpenAI(api_key=OPENAI_API_KEY)

def build_memo_with_assistant(prompt: str) -> str:
    """Generate memo using OpenAI Assistant"""
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

def strip_greeting(mini: str) -> str:
    """Remove greeting from memo for email composition"""
    m = re.search(r"(?is)\A.*?Hi GP,?\s*", mini)
    return mini[m.end():].lstrip() if m else mini.strip()

def info_round_from_prompt(prompt: str) -> str:
    """Extract round type from prompt for logging"""
    for tag in ["Pre-Seed", "Seed", "Series A", "Series B"]:
        if tag.lower() in prompt.lower():
            return tag
    return "N/A"

def process_deal(name: str, email_to: str, prompt: str) -> Dict[str, Any]:
    """Main deal processing orchestration"""
    # 1. Generate memo using OpenAI
    full_output = build_memo_with_assistant(prompt)
    
    # 2. Split into mini memo and full memo
    if "### COMPREHENSIVE INVESTMENT MEMO" in full_output:
        mini_memo, full_memo = full_output.split("### COMPREHENSIVE INVESTMENT MEMO", 1)
    else:
        mini_memo = full_output
        full_memo = full_output

    mini_memo = mini_memo.strip()
    full_memo = full_memo.strip()

    # 3. Generate PDF
    pdf_path = f"output/{name}_DealMemo.pdf"
    generate_pdf_from_text(full_memo, pdf_path)

    # 4. Extract and calibrate scoring
    scorecard = parse_score_any(mini_memo, full_memo) or {"scores": {}}
    scorecard = calibrate_scorecard(mini_memo, scorecard)

    # 5. Build combined email body
    intro_summary = extract_summary(mini_memo)
    if not intro_summary:
        intro_summary = f"Here is a mini memo for {name}. They are raising a {info_round_from_prompt(prompt)} round."

    intro = f"Hi GP,\n\n{intro_summary}\n\nFull PDF memo attached."
    mini_body = strip_greeting(mini_memo)
    mini_body = re.sub(r"(?i)^.*Full (PDF )?memo attached.*\n?", "", mini_body, flags=re.M)
    score_block = build_decision_rationale(mini_memo, scorecard)
    combined_email = "### EMAIL\n\n" + intro + "\n\n" + mini_body + "\n\n" + score_block + "\n"

    # 6. Send email
    gp_list = [e.strip() for e in (GP_RECIPIENTS or "").split(",") if e.strip()]
    if gp_list:
        send_email_oauth(
            token_path=GOOGLE_TOKEN_PATH,
            sender=GMAIL_SENDER,
            to=gp_list,
            subject=f"Deal Memo – {name} ({info_round_from_prompt(prompt)})",
            mini_memo=combined_email,
            attachment_path=pdf_path
        )

    # 7. Log to Google Sheets
    _log_to_sheets(name, mini_memo, scorecard, prompt)

    return {"ok": True, "pdf": pdf_path, "scorecard": scorecard}

def _log_to_sheets(name: str, mini_memo: str, scorecard: dict, prompt: str):
    """Extract data and log to Google Sheets"""
    # Extract key information
    summary = extract_summary(mini_memo)
    if not summary:
        summary = f"{name} is building {extract_field('Solution', mini_memo) or 'a product'}; stage: {info_round_from_prompt(prompt)}."

    traction = extract_field("Traction", mini_memo)
    team = extract_field("Team", mini_memo)
    revenue = extract_revenue(traction)
    
    # Generate tags
    round_str = info_round_from_prompt(prompt)
    tags_list = infer_tags(mini_memo, round_str)
    tags = ", ".join(tags_list) if tags_list else "AI"

    # Scoring information
    total_int = int(scorecard.get("total", 0))
    score = str(total_int)
    verdict_code = scorecard.get("verdict", "LEARN_MORE")
    action_map = {"TAKE_CALL": "📞 Take a Call", "LEARN_MORE": "⚖️ Learn More", "PASS": "❌ Pass"}
    action = action_map.get(verdict_code, "⚖️ Learn More")
    
    # Build rationale
    rationale_md = build_decision_rationale(mini_memo, scorecard)
    rationale_txt = re.sub(r"\*\*", "", rationale_md)
    rationale_txt = rationale_txt.split("Why:", 1)[-1].strip()
    rationale_txt = " ".join(x.strip("• ").strip() for x in rationale_txt.splitlines() if x.strip())
    reason = rationale_txt[:500] or "Scores driven by moat, traction, and risk profile."

    # Log to sheets
    csv_row = [
        name, summary, traction, revenue, team, round_str, 
        tags, score, "Mini memo sent", action, reason,
    ]

    append_row_oauth(
        token_path=GOOGLE_TOKEN_PATH,
        spreadsheet_id=SPREADSHEET_ID,
        range_name=SHEET_RANGE,
        values=csv_row,
    )

async def submit(info: StartupInfo, extra_context: Optional[Dict[str, Any]] = None):
    """Main entry point for deal submission"""
    prompt = build_investment_memo_prompt(info, extra_context)
    return process_deal(name=info.name, email_to=info.email_to, prompt=prompt)

# MOVED TO OTHER FILES:
# =====================
# - StartupInfo class → memo_schema.py (line 17-45)
# - _build_prompt function → utils/prompt_builder.py (line 48-200+) 
# - All scoring functions → utils/scoring_engine.py (line 270-450+)
# - Text extraction functions → field_map.py (line 470-600+)
# - Tag inference logic → field_map.py (line 630-680+)
# - Section aliases and constants → field_map.py (line 400-460+)
# - Team analysis helpers → utils/prompt_builder.py (line 220-270+)

# WHAT REMAINS:
# =============
# - Core orchestration logic (process_deal, submit)
# - OpenAI API interaction (build_memo_with_assistant) 
# - Simple utility functions (strip_greeting, info_round_from_prompt)
# - Google Sheets logging logic (_log_to_sheets)

# DEPENDENCIES:
# =============
# This file now depends on:
# - memo_schema.py (for StartupInfo model)
# - utils/prompt_builder.py (for prompt construction)
# - utils/scoring_engine.py (for scoring logic)  
# - field_map.py (for text extraction)
# - utils/config.py (configuration)
# - utils/pdf.py, utils/email.py, utils/sheet.py (integrations)