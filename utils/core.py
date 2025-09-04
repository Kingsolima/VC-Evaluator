from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time
from openai import OpenAI
from memo_schema import MemoPayload
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
{competition}

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
{university} -> Also try to get their experience and previous companies

🚩 **Red Flags / Risks**
{extra.get("risks", "")}

🧪 **Product Stage**
{extra.get("product_stage", "")}

📊 📊 **Scorecard (computed)**
Compute scores using this rubric (max points):
- Team 0-25
    - Founders/CEO/CTO/VP of Engineering (0-15)

        - 12-15: Top-decile track record in relevant scenarios; elite recruiting magnet; shipped/operated at scale; excellent commercial instincts.
        - 9-11: Strong/top-quartile performance or senior leadership roles in related domains.
        - 4-8: Success in less-relevant roles; partial proof.
        - 0-3: Limited evidence for success in this context.
    - Executive Team (non founders) (0-10)
        - 8-10: Complementary skills (product, eng, sales, ops, finance), prior scale experience, referenceable wins, velocity.
        - 4-7: Good but with gaps to fill.
        - 0-3: Thin bench, single-threaded, or heavy contractor reliance. Or any serious leadership risk
- Market 0-20
    - 16-20 for a company that has secured paying customers, or rapid customer adoption. The market is large (in the billions) and growing.
    - 9-15 Company is in testing and in beta/non paying customers/or paid pilots. The market is large (in the billions) and growing.
    - 0-8 company has little to no customer feedback. Or the market is small (in the millions) and not growing fast enough.
- Traction 0-20
    - 14-20 for a company that has made significant progress given the amount of capital raised to date in traction, such as a large user base, high engagement, or high revenue.
    - 8-13 for a company that has moderate progress given the amount of capital raised to date in traction,, such as a growing user base, moderate engagement, or moderate revenue.
    - 0-7 for a company that has weak little progress given the amount of capital raised to date in traction, such as a small user base, low engagement, or low revenue.
- Business Model 0-10
    - 8-10 for a company that has unit economics and high scalability.
    - 4-7 for a company that has unit economics but questioable scalability (or vice versa).
    - 0-3 for a company that has questionable unit economics and scalability.
- Moat 0-25
    - 20-25 for a company that has a strong moat, such as a proprietary technology, technical complexity, IP, regulations, strong brand, or network effects.
    - 15-20 for a company that has average, moderate defensability, competitors can enter market but gaining traction is relatively expensive or time intensive.
    - 10-15 for a company that has a weak moat, such as a commodity product, low technical complexity, no IP, no regulations, no strong brand, or no network effects. And competitors can easily enter the market wihout much effort, time, or cost.
    - 0-10 for a company that has no moat, such as a commodity product, low technical complexity, no IP, no regulations, no strong brand, or no network effects.
- Risk Adjustment 0 to -15 (if their isnt much risk dont adjust much, like 10 is for extreme cases)
    - Some reasons to adjust down:
        - The company is in a highly regulated industry.
        - The startup's main product can be just a feature in large companies. For example, Fetii is a rideshare app that allows riders to get vans so large groups can travel together, but this is something that Uber or Lyft can easily accomplish as a feature.
        - The startup has a low moat and low traction.
        - The founders have limited experience in the industry.
        - The founders are old (50+).

- Bonus 0 to +10
    - +5 to +10 for a strong moat but very early stage and low traction. Like Starcloud who is build data centres in space but hasnt made any revenue yet.
    - 0 to +5 is up to the evaluator to decide.
Rules:
- Total = sum(all above) bounded to 0…100.
- Verdict mapping:
  - total ≥ 80 → "TAKE A CALL"
  - 70-79 → "LEARN MORE"
  - 50-70 → "PASS"

After the email text, output ONE and only ONE ```json code block that matches this schema (all keys present, even if "N/A"):
{ MemoPayload }

Do not include any markdown/table/bullet scorecard in the email body.
After the email text, output ONE json code block ONLY for scoring.

Allowed verdicts: TAKE_CALL, LEARN_MORE, PASS.

```json -> ### Make it look like a table ###
{{"scores": {{"team": 0, "market": 0, "product": 0, "vision": 0, "traction": 0, "business_model": 0, "moat": 0, "risk_adj": 0, "bonus": 0}}, "total": 0, "verdict": "LEARN_MORE"}}


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
**{cap_table}**
- **Exit Strategy**
{vision}
{milestones}
- **Press**
{press_links}

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
            "HARD_PASS": "❌ Hard Pass",  # in case the model outputs it
        }
        return mapping.get(v, "N/A")
    for phrase in ["📞 Take a Call", "⚖️ Learn More", "❌ Pass"]:
        if phrase in text:
            return phrase
    return "N/A"


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
    headers = (r"Startup Overview|Market|Problem|Solution|Traction|Business Model|"
               r"Moat / Defensibility|Moat|Team|Red Flags|Product Stage|Scorecard|FULL DEAL MEMO")
    pat = rf"(?is)Hi GP,?\s*(.*?)(?=\n\s*(?:[^\w\s]?\s*)?\**(?:{headers})\**\b)"
    m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
    if m:
        s = m.group(1).strip()
        if s:
            return s
    return ""


#2) **Add a bullet-parser fallback + calibration** (so even if it goes markdown again, you still get a sane score)


def parse_scorecard_bullets(text: str):
    # e.g., "**Team**: 21/25" or "**Risk Adjustment**: -3"
    def grab(label, default=None, denom=None, signed=False):
        if denom:
            m = re.search(rf"\*\*{re.escape(label)}\*\*:\s*(-?\d+)\s*/\s*{denom}", text, re.I)
            return int(m.group(1)) if m else default
        else:
            rgx = rf"\*\*{re.escape(label)}\*\*:\s*([+-]?\d+)"
            m = re.search(rgx, text, re.I)
            return int(m.group(1)) if m else default

    scores = {
        "team":           grab("Team", 0, 25),
        "market":         grab("Market", 0, 20),
        "product":        grab("Product", 0, 10),
        "vision":         grab("Vision", 0, 5),
        "traction":       grab("Traction", 0, 10),
        "business_model": grab("Business Model", 0, 5),
        "moat":           grab("Moat", 0, 25),
        "risk_adj":       grab("Risk Adjustment", 0, None),
        "bonus":          grab("Bonus", 0, None),
    }
    total = sum([
        scores["team"], scores["market"], scores["product"], scores["vision"],
        scores["traction"], scores["business_model"], scores["moat"],
        scores["risk_adj"], scores["bonus"]
    ])
    # fallback verdict from total
    verdict = "TAKE_CALL" if total >= 82 else "LEARN_MORE" if total >= 70 else "PASS"
    return {"scores": scores, "total": total, "verdict": verdict}

def parse_score_any(mini: str, full: str):
    sc = parse_scorecard_json(mini) or parse_scorecard_json(full)
    if sc: return sc
    # try bullets in mini, then full
    m = parse_scorecard_bullets(mini)
    if m and isinstance(m.get("total"), int): return m
    return parse_scorecard_bullets(full)

def _parse_mrr(text: str) -> int | None:
    m = re.search(r"\$?\s*([\d.,]+)\s*([kKmM])?\s*MRR", text or "", re.I)
    if not m: return None
    n = float(m.group(1).replace(",", ""))
    unit = (m.group(2) or "").lower()
    if unit == "k": n *= 1_000
    if unit == "m": n *= 1_000_000
    return int(n)

def calibrate_scorecard(mini_memo: str, sc: dict) -> dict:
    s = (sc.get("scores") or {}).copy()
    # traction floor for Seed $100k+ MRR
    mrr = _parse_mrr(extract_field("Traction", mini_memo))
    if isinstance(mrr, int) and mrr >= 100_000:
        s["traction"] = max(s.get("traction", 0), 9)
    # clamp typical risk
    s["risk_adj"] = max(s.get("risk_adj", 0), -3)
    # moat nudge if defensibility keywords present
    moat_src = (extract_field("Moat / Defensibility", mini_memo) or "").lower()
    if any(k in moat_src for k in ["government api", "gov api", "compliance", "biometric", "white-label", "white label", "proprietary data", "dpa", "soc2", "iso 27001"]):
        s["moat"] = max(s.get("moat", 0), 20)
    total = (s.get("team",0)+s.get("market",0)+s.get("product",0)+s.get("vision",0)+
             s.get("traction",0)+s.get("business_model",0)+s.get("moat",0)+
             s.get("risk_adj",0)+s.get("bonus",0))
    verdict = "TAKE_CALL" if total >= 80 else "LEARN_MORE" if total >= 70 else "PASS"
    sc["scores"], sc["total"], sc["verdict"] = s, int(round(total)), verdict
    return sc

def build_decision_rationale(mini: str, sc: dict) -> str:
    s = sc.get("scores", {})
    reasons = []
    # negative drivers first
    if s.get("moat", 25) < 15:
        reasons.append(f"Moat is weak ({s.get('moat',0)}/25): limited defensibility articulated.")
    if s.get("risk_adj", 0) <= -3:
        reasons.append(f"Risk −{abs(s.get('risk_adj',0))}: regulated workflow / compliance exposure needs proof (DPAs/SOC2 path).")
    if s.get("business_model", 5) < 4:
        reasons.append(f"Business model unclear ({s.get('business_model',0)}/5): pricing/expansion motion needs detail.")
    # positive drivers
    tr_txt = extract_field("Traction", mini)
    mrr = _parse_mrr(tr_txt or "")
    if isinstance(mrr, int) and mrr >= 100_000:
        reasons.append(f"Strong traction (≈${mrr:,} MRR) supports demand.")
    if s.get("team",0) >= 20:
        reasons.append(f"Team strength ({s.get('team',0)}/25): credible background for execution.")
    # assemble
    verdict = sc.get("verdict","LEARN_MORE")
    total = sc.get("total","N/A")
    head = f"**Score: {total}/100 → Recommendation: " + ({"TAKE_CALL":"📞 Take a Call","LEARN_MORE":"⚖️ Learn More","PASS":"❌ Pass"}[verdict]) + "**"
    body = "• " + "\n• ".join(reasons[:4]) if reasons else "• Results driven by current subscores across moat, traction, and risk."
    return head + "\n\n**Why:**\n" + body

def strip_greeting(mini: str) -> str:
    m = re.search(r"(?is)\A.*?Hi GP,?\s*", mini)
    return mini[m.end():].lstrip() if m else mini.strip()

# Accept common variations of section headers
# Aliases (keep these above)
SECTION_ALIASES = {
    "Startup Overview": ["Startup Overview", "Overview"],
    "Market": ["Market", "Market Opportunity", "Addressable Market", "TAM", "Market Size"],
    "Problem": ["Problem", "Pain", "Problem & Solution"],
    "Solution": ["Solution", "Product", "What We Do"],
    "Traction": ["Traction", "Traction & Milestones", "Revenue, Contracts & Pipeline",
                 "Revenue & Pipeline", "Revenue", "Milestones"],
    "Business Model": ["Business Model", "Biz Model", "Monetization", "Pricing"],
    "Moat / Defensibility": ["Moat / Defensibility", "Moat", "Defensibility", "Unfair Advantage"],
    "Team": ["Team", "Founders", "Founders, Team, and Advisors", "Team & Advisors", "Leadership"],
    "Red Flags / Risks": ["Red Flags / Risks", "Risks", "Risk"],
    "Product Stage": ["Product Stage", "Stage"],
}

ALL_HEADERS = sorted({h for k, vs in SECTION_ALIASES.items() for h in ([k] + vs)},
                     key=len, reverse=True)

def extract_field(label: str, text: str) -> str:
    """
    Find the block after a header matching `label` or any alias, until the next known header.
    Handles optional emoji and **bold** in headings.
    """
    labels = SECTION_ALIASES.get(label, [label])

    # Build the alternations for CURRENT header and for the lookahead to the NEXT header
    label_re = "(?:" + "|".join(re.escape(x) for x in labels) + ")"
    next_re  = "(?:" + "|".join(re.escape(x) for x in ALL_HEADERS) + ")"

    # A header line: optional emoji/symbol, optional spaces, optional **bold**
    header = rf"^\s*(?:[🏷️📈🔍🛠📊💵🧱👥🚩🧪]\s*)?\**{label_re}\**\s*$"

    # Capture everything after that header until the next header or end of text
    pattern = rf"(?ims){header}\n+(.*?)(?=^\s*(?:[🏷️📈🔍🛠📊💵🧱👥🚩🧪]\s*)?\**(?:{next_re})\**\s*$|\Z)"

    m = re.search(pattern, text)
    return m.group(1).strip() if m else "Unknown"

def extract_field(label: str, text: str) -> str:
    """
    Extract the block after a header that matches `label` or any of its aliases.
    Emoji and **bold** are optional; match until the next known header or end of text.
    """
    labels = SECTION_ALIASES.get(label, [label])
    label_re = "|".join(re.escape(x) for x in labels)
    next_re  = "|".join(re.escape(x) for x in ALL_HEADERS)
    # optional emoji/symbols at start, optional **bold**
    header = rf"^\s*(?:[🏷️📈🔍🛠📊💵🧱👥🚩🧪]\s*)?\**{re.escape(label)}\**\s*$"
    pattern = rf"(?ims){header}\n+(.*?)(?=^\s*(?:[🏷️📈🔍🛠📊💵🧱👥🚩🧪]\s*)?\**(?:{next_headers})\**\s*$|\Z)"
    m = re.search(pattern, text)
    return m.group(1).strip() if m else "Unknown"

# --- TAGGING ---------------------------------------------------------------
# --- Auto-tagging -----------------------------------------------------------
TAG_RULES = [
    (r"\bvisa|passport|immigration|e[- ]?visa|airline|ota\b",            "TravelTech"),
    (r"\bgeospatial|earth ?observation|satellite|sar\b",                 "Geospatial"),
    (r"\bspace[- ]?(force|domain|tech)|orbit|ssa\b",                     "SpaceTech"),
    (r"\bdefen[cs]e|dod|usaf|us space force|nato|militar(y|ies)\b",      "DefenseTech"),
    (r"\bgovernment|public sector|procure(ment)?\b",                     "GovTech"),
    (r"\bcompliance|regulator(y|ies)|soc[- ]?2|iso ?27001|dpa\b",        "RegTech"),
    (r"\bbiometric|facial recognition|face match\b",                     "Biometrics"),
    (r"\brpa\b|\bautomation|workflow\b",                                 "Automation"),
    (r"\bcomputer vision|object detection|imag(e|ing)\b",                "Computer Vision"),
    (r"\bnlp|llm|language model|gpt\b",                                  "NLP"),
    (r"\bapi\b",                                                         "API"),
    (r"\bsaas|subscription|per[- ]?(seat|user)\b",                        "SaaS"),
    (r"\bb2g\b|agency\b|contract\b",                                     "B2G"),
    (r"\bb2b2c\b",                                                       "B2B2C"),
    (r"\bb2b\b|enterprise\b",                                            "B2B"),
    (r"\bf(in|)tech|payment|invoice|billing\b",                          "FinTech"),
    (r"\binsurtech|insurance\b",                                         "InsurTech"),
    (r"\bhealthtech|patient|hospital|clinical\b",                        "HealthTech"),
]

def infer_tags(
    mini_memo: str,
    info: "StartupInfo",
    extra: Optional[Dict[str, Any]] = None,
    max_tags: int = 8,
) -> List[str]:
    """Heuristic tags from the memo + context."""
    text = " ".join(filter(None, [
        mini_memo,
        getattr(info, "product", ""),
        getattr(info, "investors", ""),
        (extra or {}).get("market", "")
    ])).lower()

    tags: List[str] = []

    # universal AI detection
    if re.search(r"\b(ai|machine learning|ml|deep learning)\b", text):
        tags.append("AI")

    # rule-based tags
    for pattern, tag in TAG_RULES:
        if re.search(pattern, text, re.IGNORECASE):
            tags.append(tag)

    # stage tag (optional)
    if getattr(info, "round", ""):
        tags.append(info.round.strip().title())

    # dedupe & cap
    seen = set()
    uniq: List[str] = []
    for t in tags:
        if t not in seen:
            uniq.append(t); seen.add(t)
    return uniq[:max_tags]



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

        # ---------- build combined email body ----------
    # 1) intro paragraph (merge the “two emails”)
    intro_summary = extract_summary(mini_memo)
    if not intro_summary:
        # safe fallback if model didn’t provide a good summary
        intro_summary = f"Here is a mini memo for {name}. They are raising a {info_round_from_prompt(prompt)} round, with interest from {extract_field('Startup Overview', mini_memo) or 'notable investors'}."

    intro = f"Hi GP,\n\n{intro_summary}\n\nFull PDF memo attached."

    # 2) keep the model’s sections but strip greeting/header duplication
    mini_body = strip_greeting(mini_memo)
    # drop any 'Full PDF memo attached' lines from the model body to avoid duplicates
    mini_body = re.sub(r"(?i)^.*Full (PDF )?memo attached.*\n?", "", mini_body, flags=re.M)

    # 3) scoring + rationale (deterministic)
    sc = parse_score_any(mini_memo, full_memo) or {"scores": {}}
    sc = calibrate_scorecard(mini_memo, sc)
    score_block = build_decision_rationale(mini_memo, sc)

    combined_email = "### EMAIL\n\n" + intro + "\n\n" + mini_body + "\n\n" + score_block + "\n"

    # ---------- send one email ----------
    gp_list = [e.strip() for e in (GP_RECIPIENTS or "").split(",") if e.strip()]
    if not gp_list:
        raise RuntimeError("No GP_RECIPIENTS set; refusing to send.")
    recipients = gp_list
    # Send email
    # Prefer explicit GP recipients from env; do NOT email founder by default
    # if empty, nothing is sent; that’s safer than emailing founder

    send_email_oauth (
    token_path=GOOGLE_TOKEN_PATH,
    sender=GMAIL_SENDER,
    to=recipients,
    subject=f"Deal Memo – {name} ({info_round_from_prompt(prompt)})",
    mini_memo=combined_email,   # ← was mini_memo
    attachment_path=pdf_path
    )


        # Extract data and log to Google Sheets

    # Robust intro summary
    summary = extract_summary(mini_memo)
    if not summary:
        summary = (
            f"{name} is building {extract_field('Solution', mini_memo) or 'an AI product'}; "
            f"stage: {info_round_from_prompt(prompt)}; "
            f"traction: {extract_field('Traction', mini_memo)}; "
            f"backed by {extract_field('Startup Overview', mini_memo) or 'notable investors'}."
        )

    traction = extract_field("Traction", mini_memo)
    team     = extract_field("Team", mini_memo)
    revenue  = extract_revenue(traction)

    round_str = info_round_from_prompt(prompt)
    tags_list = infer_tags(
    mini_memo,
    product="",        # if you have this handy, pass it
    investors="",      # same here
    market="",         # or pass extra_context['market'] if you thread it through
    round_str=round_str,
    )
    tags = ", ".join(tags_list) if tags_list else "AI"



    # If the model used a different header, try common alternates explicitly
    if traction == "Unknown":
        traction = extract_field("Revenue, Contracts & Pipeline", mini_memo)  # alias handled too

    # If we still couldn't find explicit revenue, search the whole memo
    if revenue == "Unknown":
        revenue = extract_revenue(mini_memo)

    if team == "Unknown":
        team = extract_field("Founders", mini_memo)  # covered by aliases



    # Parse scorecard from mini or full, then calibrate
    scorecard = parse_score_any(mini_memo, full_memo) or {"scores": {}}
    scorecard = calibrate_scorecard(mini_memo, scorecard)

    # Numeric score for Sheets
    total_int = int(scorecard.get("total", 0))
    score     = str(total_int)

    # Human-facing action label from verdict code
    verdict_code = scorecard.get("verdict", "LEARN_MORE")
    action_map   = {"TAKE_CALL":"📞 Take a Call", "LEARN_MORE":"⚖️ Learn More", "PASS":"❌ Pass"}
    action       = action_map.get(verdict_code, "⚖️ Learn More")

    # Concise rationale for the Sheet (use the same logic as email, but flatten)
    rationale_md = build_decision_rationale(mini_memo, scorecard)  # markdown block
    # Strip headings/bullets and condense to one line
    rationale_txt = re.sub(r"\*\*", "", rationale_md)                 # remove bold markers
    rationale_txt = rationale_txt.split("Why:", 1)[-1].strip()         # keep the reasons
    rationale_txt = " ".join(x.strip("• ").strip() for x in rationale_txt.splitlines() if x.strip())
    reason        = rationale_txt[:500] or "Scores driven by moat, traction, and risk profile."

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
        reason,
    ]

    append_row_oauth(
        token_path=GOOGLE_TOKEN_PATH,
        spreadsheet_id=SPREADSHEET_ID,
        range_name=SHEET_RANGE,
        values=csv_row,
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
