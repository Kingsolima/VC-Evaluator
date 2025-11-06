# field_map.py - Enhanced with text extraction functions from core.py
import re
from typing import Dict

# Existing field mapping
FIELD_ID_MAP = {
    # Contact
    "Wv0KJokmEgXf": "first_name",
    "l7veVq4q4lgB": "last_name", 
    "4Jb9HHo52T8C": "founder_email",
    "DWzmnLF1knFo": "incorporation",

    # Company
    "mzHp4Tu0OoYM": "name",
    "c9HlEwfySxtL": "website",

    # Role / Round
    "Qx09I8wJFNK8": "position",
    "mUYVKWT1i9PP": "round",

    # Investors
    "zLSUDjGaXv6d": "investors",

    # Pitch content
    "dVeAPHMXoR2w": "problem",
    "oYO4cXbcGLXm": "solution", 
    "pCZ3KBTQswM6": "market",
    "iJYrxnJX3GSH": "traction",
    "lPiAAh47JduK": "team",
    "rrZqT9pPUwMR": "university",
    "fHSrbZW4a1Yd": "competition",
    "zFWGX1jtHF0b": "milestones",
    "sKaECsQtK6xQ": "vision",

    # File upload
    "sBbesO8XqPq9": "pitch_deck_url",
    
    # NEW: Early stage form fields
    "industry": "industry",
    "round_size": "round_size", 
    "revenue": "revenue",
    "customers": "customers",
    "market_size": "market_size",
    "business_model": "business_model",
    "moat": "moat",
    "risks": "risks",
    "product_stage": "product_stage",
    "pitch_deck": "pitch_deck",
    
    # Founder fields
    "founder_1_name": "founder_1_name",
    "founder_1_background": "founder_1_background",
    "founder_1_linkedin": "founder_1_linkedin",
    "founder_2_name": "founder_2_name", 
    "founder_2_background": "founder_2_background",
    "founder_2_linkedin": "founder_2_linkedin",
    "founder_3_name": "founder_3_name",
    "founder_3_background": "founder_3_background", 
    "founder_3_linkedin": "founder_3_linkedin",
}

# Text extraction functions (moved from core.py)
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
    Extract the block after a header that matches `label` or any of its aliases.
    Handles optional emoji and **bold** in headings.
    """
    labels = SECTION_ALIASES.get(label, [label])
    label_re = "|".join(re.escape(x) for x in labels)
    next_re = "|".join(re.escape(x) for x in ALL_HEADERS)
    
    # Header pattern with optional emoji/bold
    header = rf"^\s*(?:[🏷️📈🔍🛠📊💵🧱👥🚩🧪]\s*)?\**({label_re})\**\s*$"
    pattern = rf"(?ims){header}\n+(.*?)(?=^\s*(?:[🏷️📈🔍🛠📊💵🧱👥🚩🧪]\s*)?\**(?:{next_re})\**\s*$|\Z)"
    
    m = re.search(pattern, text)
    return m.group(1).strip() if m else "Unknown"

def extract_revenue(traction_text: str) -> str:
    """Extract revenue metrics from traction text"""
    patterns = [
        r"\$[0-9][0-9,\.]*\s*[kKmM]?\s*(?:ARR|MRR|annual|monthly)?",
        r"[0-9][0-9,\.]*\s*(?:users|customers|clients)\b",
        r"\b[0-9]+\s*(?:paying customers|subs|subscriptions)\b"
    ]
    for pattern in patterns:
        m = re.search(pattern, traction_text, re.IGNORECASE)
        if m:
            return m.group(0)
    return "Unknown"

def extract_summary(text: str) -> str:
    """Extract summary from between 'Hi GP,' and first header"""
    headers = (r"Startup Overview|Market|Problem|Solution|Traction|Business Model|"
               r"Moat / Defensibility|Moat|Team|Red Flags|Product Stage|Scorecard|FULL DEAL MEMO")
    pat = rf"(?is)Hi GP,?\s*(.*?)(?=\n\s*(?:[^\w\s]?\s*)?\**(?:{headers})\**\b)"
    m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
    if m:
        s = m.group(1).strip()
        if s:
            return s
    return ""

# Auto-tagging rules
TAG_RULES = [
    (r"\bvisa|passport|immigration|e[- ]?visa|airline|ota\b", "TravelTech"),
    (r"\bgeospatial|earth ?observation|satellite|sar\b", "Geospatial"),
    (r"\bspace[- ]?(force|domain|tech)|orbit|ssa\b", "SpaceTech"),
    (r"\bdefen[cs]e|dod|usaf|us space force|nato|militar(y|ies)\b", "DefenseTech"),
    (r"\bgovernment|public sector|procure(ment)?\b", "GovTech"),
    (r"\bcompliance|regulator(y|ies)|soc[- ]?2|iso ?27001|dpa\b", "RegTech"),
    (r"\bbiometric|facial recognition|face match\b", "Biometrics"),
    (r"\brpa\b|\bautomation|workflow\b", "Automation"),
    (r"\bcomputer vision|object detection|imag(e|ing)\b", "Computer Vision"),
    (r"\bnlp|llm|language model|gpt\b", "NLP"),
    (r"\bapi\b", "API"),
    (r"\bsaas|subscription|per[- ]?(seat|user)\b", "SaaS"),
    (r"\bb2g\b|agency\b|contract\b", "B2G"),
    (r"\bb2b2c\b", "B2B2C"),
    (r"\bb2b\b|enterprise\b", "B2B"),
    (r"\bf(in|)tech|payment|invoice|billing\b", "FinTech"),
    (r"\binsurtech|insurance\b", "InsurTech"),
    (r"\bhealthtech|patient|hospital|clinical\b", "HealthTech"),
]

def infer_tags(text: str, round_str: str = "", max_tags: int = 8) -> list[str]:
    """Generate tags from text content"""
    tags = []
    text_lower = text.lower()
    
    # Universal AI detection
    if re.search(r"\b(ai|machine learning|ml|deep learning)\b", text_lower):
        tags.append("AI")
    
    # Rule-based tags
    for pattern, tag in TAG_RULES:
        if re.search(pattern, text_lower, re.IGNORECASE):
            tags.append(tag)
    
    # Stage tag
    if round_str:
        tags.append(round_str.strip().title())
    
    # Dedupe and limit
    seen = set()
    unique_tags = []
    for tag in tags:
        if tag not in seen:
            unique_tags.append(tag)
            seen.add(tag)
    
    return unique_tags[:max_tags]