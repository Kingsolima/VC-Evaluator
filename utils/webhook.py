# utils/webhook.py
import logging, traceback, time, asyncio
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

@router.post("/typeform-webhook")
async def typeform_webhook(request: Request, background_tasks: BackgroundTasks):
    result: Dict[str, Any] = {"ok": False}
    try:
        payload: Dict[str, Any] = await request.json()
        dry_run = request.query_params.get("dry_run") in ("1", "true", "True")
        form_response = payload.get("form_response") or {}
        rid = (payload.get("event_id")
            or form_response.get("token")
            or form_response.get("response_id"))

        if rid and _seen(rid):
            return {"ok": True, "dedup": True}

        parsed = extract_answers_by_id(form_response)
        result.update({"ok": True, "dry_run": dry_run, "parsed_answers": parsed})

        if dry_run:
            result["note"] = "Dry run: not calling OpenAI/Email/PDF/Sheets."
            return result

        from utils.core import submit, StartupInfo

        info = StartupInfo(
            name      = parsed.get("name", "NA"),
            website   = parsed.get("website", "NA"),
            round     = parsed.get("round", "Seed"),
            investors = parsed.get("investors", "N/A"),
            traction  = parsed.get("traction", ""),
            team      = parsed.get("team", ""),
            product   = parsed.get("solution", ""),
            email_to  = ""  # don't route to founder
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

        # queue the heavy work; return 200 immediately so no retries
        background_tasks.add_task(asyncio.create_task, submit(info, extra_context=extra))
        return {"ok": True, "queued": True, "rid": rid}

    except Exception as e:
        result["error"] = str(e)
        result["trace"] = traceback.format_exc()
        return result
