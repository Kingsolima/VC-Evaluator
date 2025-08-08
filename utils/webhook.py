# utils/webhook.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from utils.core import submit, StartupInfo
from utils.field_map import FIELD_ID_MAP

router = APIRouter()

def _extract_value(answer: Dict[str, Any]) -> str:
    """
    Return a string value from a Typeform answer, covering common answer types.
    """
    # Simple primitives
    for k in ("text", "email", "url", "number", "boolean", "phone_number"):
        if answer.get(k) not in (None, ""):
            return str(answer[k]).strip()

    # Single choice
    choice = answer.get("choice")
    if isinstance(choice, dict) and choice.get("label"):
        return str(choice["label"]).strip()

    # 'choices' (multi) -> join labels
    choices = answer.get("choices", {}).get("labels")
    if isinstance(choices, list) and choices:
        return ", ".join([str(x).strip() for x in choices])

    # File upload (different shapes occur)
    if "file_url" in answer and answer["file_url"]:
        return str(answer["file_url"]).strip()
    files = answer.get("files")
    if isinstance(files, list) and files:
        # try url under item (varies by integration)
        for f in files:
            url = f.get("url") or f.get("file_url")
            if url:
                return str(url).strip()

    # Fallback: stringify whole answer (debug)
    return str(answer)

def extract_answers_by_id(form_response: Dict[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for a in form_response.get("answers", []):
        fid = (a.get("field") or {}).get("id")
        key = FIELD_ID_MAP.get(fid)
        if not key:
            continue
        out[key] = _extract_value(a)
    return out

@router.post("/typeform-webhook")
async def typeform_webhook(payload: Dict[str, Any]):
    try:
        data = extract_answers_by_id(payload.get("form_response", {}))

        # Build required object for core
        info = StartupInfo(
            name=data.get("name", "NA"),
            website=data.get("website", "NA"),
            round=data.get("round", "Seed"),
            investors=data.get("investors", "N/A"),
            traction=data.get("traction", ""),
            team=data.get("team", ""),
            product=data.get("solution", ""),  # short product line
            email_to=data.get("founder_email", "")  # you can CC your GP list in core
        )

        # Pass the rest as extra context
        extra_context = {
            "first_name":     data.get("first_name", ""),
            "last_name":      data.get("last_name", ""),
            "founder_email":  data.get("founder_email", ""),
            "incorporation":  data.get("incorporation", ""),
            "position":       data.get("position", ""),
            "problem":        data.get("problem", ""),
            "solution":       data.get("solution", ""),
            "market":         data.get("market", ""),
            "team_detail":    data.get("team", ""),
            "university":     data.get("university", ""),
            "competition":    data.get("competition", ""),
            "milestones":     data.get("milestones", ""),
            "vision":         data.get("vision", ""),
            "pitch_deck_url": data.get("pitch_deck_url", ""),
            # optional future keys:
            # "industry": data.get("industry", ""),
            # "round_size": data.get("round_size", ""),
            # "business_model": data.get("business_model", ""),
            # "product_stage": data.get("product_stage", ""),
            # "moat": data.get("moat", ""),
            # "risks": data.get("risks", ""),
            # "cap_table": data.get("cap_table", ""),
            # "press_links": data.get("press_links", ""),
        }

        return await submit(info, extra_context=extra_context)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
