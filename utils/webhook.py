# utils/webhook.py
import logging, traceback
from fastapi import APIRouter, Request
from typing import Dict, Any
from utils.field_map import FIELD_ID_MAP

logger = logging.getLogger("webhook")
logging.basicConfig(level=logging.INFO)

router = APIRouter()

@router.get("/ping")
async def ping():
    return {"ok": True}

def _extract_value(a: Dict[str, Any]) -> str:
    for k in ("text", "email", "url", "number", "boolean", "phone_number"):
        v = a.get(k)
        if v not in (None, ""):
            return str(v).strip()
    ch = a.get("choice")
    if isinstance(ch, dict) and ch.get("label"):
        return str(ch["label"]).strip()
    labels = (a.get("choices") or {}).get("labels")
    if isinstance(labels, list) and labels:
        return ", ".join([str(x).strip() for x in labels])
    if a.get("file_url"):
        return str(a["file_url"]).strip()
    files = a.get("files")
    if isinstance(files, list) and files:
        for f in files:
            url = f.get("url") or f.get("file_url")
            if url:
                return str(url).strip()
    return str(a)

def extract_answers_by_id(form_response: Dict[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for a in form_response.get("answers", []):
        fid = (a.get("field") or {}).get("id")
        key = FIELD_ID_MAP.get(fid)
        if not key:
            out[f"UNMAPPED::{fid}"] = _extract_value(a)
            continue
        out[key] = _extract_value(a)
    return out

@router.post("/typeform-webhook")
async def typeform_webhook(request: Request):
    # Always return 200 with details while debugging — no 500s.
    result: Dict[str, Any] = {"ok": False}
    try:
        payload: Dict[str, Any] = await request.json()
        dry_run = request.query_params.get("dry_run") in ("1", "true", "True")
        form_response = payload.get("form_response") or {}
        rid = (payload.get("event_id")
            or form_response.get("token")
            or form_response.get("response_id"))

        if rid and _seen(rid):
            # already processed this submission
            return {"ok": True, "dedup": True}

        parsed = extract_answers_by_id(form_response)

        result.update({
            "ok": True,
            "dry_run": dry_run,
            "parsed_answers": parsed,
        })

        if dry_run:
            # Do NOT import core or call anything external.
            result["note"] = "Dry run: not calling OpenAI/Email/PDF/Sheets."
            return result

        # Only import heavy deps when we actually need them
        from utils.core import submit, StartupInfo

        info = StartupInfo(
            name      = parsed.get("name", "NA"),
            website   = parsed.get("website", "NA"),
            round     = parsed.get("round", "Seed"),
            investors = parsed.get("investors", "N/A"),
            traction  = parsed.get("traction", ""),
            team      = parsed.get("team", ""),
            product   = parsed.get("solution", ""),
            email_to  = parsed.get("founder_email", "")
        )

        extra = {
            "first_name":     parsed.get("first_name",""),
            "last_name":      parsed.get("last_name",""),
            "founder_email":  parsed.get("founder_email",""),
            "incorporation":  parsed.get("incorporation",""),
            "position":       parsed.get("position",""),
            "problem":        parsed.get("problem",""),
            "solution":       parsed.get("solution",""),
            "market":         parsed.get("market",""),
            "team_detail":    parsed.get("team",""),
            "university":     parsed.get("university",""),
            "competition":    parsed.get("competition",""),
            "milestones":     parsed.get("milestones",""),
            "vision":         parsed.get("vision",""),
            "pitch_deck_url": parsed.get("pitch_deck_url",""),
        }

        result["startup_info"] = info.dict()
        result["extra_context"] = extra

        # Call the full pipeline
        submit_result = await submit(info, extra_context=extra)
        result["submit_result"] = submit_result
        return result

    except Exception as e:
        # Return the error in the body (HTTP 200) so you can see it without paid logs
        result["error"] = str(e)
        result["trace"] = traceback.format_exc()
        return result  # 200 with error details
