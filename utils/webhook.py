# utils/webhook.py
import logging, traceback, time
from fastapi import APIRouter, Request, BackgroundTasks
from typing import Dict, Any
from utils.field_map import FIELD_ID_MAP

router = APIRouter()
SEEN: Dict[str, float] = {}

def _seen(id_: str, ttl: int = 600) -> bool:
    now = time.time()
    for k, v in list(SEEN.items()):
        if v < now:
            SEEN.pop(k, None)
    if not id_:
        return False
    if id_ in SEEN:
        return True
    SEEN[id_] = now + ttl
    return False

# 🔧 bring back the parser utilities
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
        out[key or f"UNMAPPED::{fid}"] = _extract_value(a)
    return out

@router.post("/typeform-webhook")
async def typeform_webhook(request: Request, background_tasks: BackgroundTasks):
    payload: Dict[str, Any] = await request.json()
    dry_run = request.query_params.get("dry_run") in ("1", "true", "True")
    form_response = payload.get("form_response") or {}
    rid = (payload.get("event_id")
           or form_response.get("token")
           or form_response.get("response_id"))

    if rid and _seen(rid):
        return {"ok": True, "dedup": True}

    parsed = extract_answers_by_id(form_response)

    if dry_run:
        return {"ok": True, "dry_run": True, "parsed_answers": parsed}

    from utils.core import submit, StartupInfo
    info = StartupInfo(
        name=parsed.get("name","NA"), website=parsed.get("website","NA"),
        round=parsed.get("round","Seed"), investors=parsed.get("investors","N/A"),
        traction=parsed.get("traction",""), team=parsed.get("team",""),
        product=parsed.get("solution",""), email_to=""
    )
    extra = {
        "first_name": parsed.get("first_name",""),
        "last_name": parsed.get("last_name",""),
        "founder_email": parsed.get("founder_email",""),
        "incorporation": parsed.get("incorporation",""),
        "position": parsed.get("position",""),
        "problem": parsed.get("problem",""),
        "solution": parsed.get("solution",""),
        "market": parsed.get("market",""),
        "team_detail": parsed.get("team",""),
        "university": parsed.get("university",""),
        "competition": parsed.get("competition",""),
        "milestones": parsed.get("milestones",""),
        "vision": parsed.get("vision",""),
        "pitch_deck_url": parsed.get("pitch_deck_url",""),
    }

    # ✅ queue the coroutine directly (don’t wrap with asyncio.create_task)
    background_tasks.add_task(submit, info, extra_context=extra)
    return {"ok": True, "queued": True, "rid": rid}
