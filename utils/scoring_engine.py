# utils/scoring_engine.py - Scoring and parsing logic extracted from core.py
import re
import json
from typing import Dict, Any, Optional
from field_map import extract_field

def parse_scorecard_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON scorecard from text - moved from core.py"""
    # Look for the last fenced JSON block
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if not m:
        # Fallback: any fenced block
        m = re.search(r"```\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None

def parse_scorecard_bullets(text: str):
    """Fallback bullet parser for scoring - moved from core.py"""
    def grab(label, default=None, denom=None):
        if denom:
            m = re.search(rf"\*\*{re.escape(label)}\*\*:\s*(-?\d+)\s*/\s*{denom}", text, re.I)
            return int(m.group(1)) if m else default
        else:
            rgx = rf"\*\*{re.escape(label)}\*\*:\s*([+-]?\d+)"
            m = re.search(rgx, text, re.I)
            return int(m.group(1)) if m else default

    scores = {
        "team": grab("Team", 0, 25),
        "market": grab("Market", 0, 20),
        "product": grab("Product", 0, 10),
        "vision": grab("Vision", 0, 5),
        "traction": grab("Traction", 0, 10),
        "business_model": grab("Business Model", 0, 5),
        "moat": grab("Moat", 0, 25),
        "risk_adj": grab("Risk Adjustment", 0, None),
        "bonus": grab("Bonus", 0, None),
    }
    
    total = sum(scores[k] for k in scores.keys())
    verdict = "TAKE_CALL" if total >= 80 else "LEARN_MORE" if total >= 70 else "PASS"
    return {"scores": scores, "total": total, "verdict": verdict}

def parse_score_any(mini: str, full: str):
    """Parse scorecard from either mini or full memo - moved from core.py"""
    sc = parse_scorecard_json(mini) or parse_scorecard_json(full)
    if sc: 
        return sc
    # Try bullets in mini, then full
    m = parse_scorecard_bullets(mini)
    if m and isinstance(m.get("total"), int): 
        return m
    return parse_scorecard_bullets(full)

def _parse_mrr(text: str) -> Optional[int]:
    """Parse MRR from text - moved from core.py"""
    m = re.search(r"\$?\s*([\d.,]+)\s*([kKmM])?\s*MRR", text or "", re.I)
    if not m: 
        return None
    n = float(m.group(1).replace(",", ""))
    unit = (m.group(2) or "").lower()
    if unit == "k": 
        n *= 1_000
    if unit == "m": 
        n *= 1_000_000
    return int(n)

def calibrate_scorecard(mini_memo: str, sc: dict) -> dict:
    """Apply business logic calibrations to scores - moved from core.py"""
    s = (sc.get("scores") or {}).copy()
    
    # Traction floor for Seed $100k+ MRR
    mrr = _parse_mrr(extract_field("Traction", mini_memo))
    if isinstance(mrr, int) and mrr >= 100_000:
        s["traction"] = max(s.get("traction", 0), 9)
    
    # Clamp typical risk
    s["risk_adj"] = max(s.get("risk_adj", 0), -3)