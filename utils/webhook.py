from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from utils.core import submit, StartupInfo

router = APIRouter()

class TypeformSubmission(BaseModel):
    form_response: Dict[str, Any]

def extract_answers(form_response: Dict[str, Any]) -> Dict[str, str]:
    answers = {}
    for a in form_response.get("answers", []):
        q_title = a.get("field", {}).get("title", "").strip()
        value = (
            a.get("text") or
            a.get("email") or
            a.get("number") or
            a.get("choice", {}).get("label") or
            str(a)
        )
        answers[q_title] = value
    return answers

@router.post("/typeform-webhook")
async def typeform_webhook(submission: TypeformSubmission):
    try:
        answers = extract_answers(submission.form_response)

        info = StartupInfo(
            name=answers.get("Company Name ?", "NA"),
            website=answers.get("Company website?", "NA"),
            round=answers.get("Which series are you looking to raise?", "NA"),
            investors=answers.get("Do you have a lead investor for this round? If so, please include their name", "NA"),
            traction=answers.get("Traction", "NA"),
            team=answers.get("Team", "NA"),
            product=answers.get("Solution", "NA"),
            email_to="gp1@example.com"  # Replace with your actual GP email or list
        )

        # Extra context for AI memo
        extra_context = {
            "first_name": answers.get("What's your first name?", ""),
            "last_name": answers.get("What's your last name?", ""),
            "founder_email": answers.get("What's your email address, Omar?", ""),
            "incorporation": answers.get("Where is the company incorporated?", ""),
            "position": answers.get("Position in the company?", ""),
            "problem": answers.get("Problem", ""),
            "solution": answers.get("Solution", ""),
            "market": answers.get("Market", ""),
            "team_detail": answers.get("Team", ""),
            "university": answers.get("What university did you attend?", ""),
            "competition": answers.get("Competition", ""),
            "milestones": answers.get("Milestones to Next Round", ""),
            "vision": answers.get("Vision", "")
            # Pitch Deck would be a file URL from Typeform — separate handling
        }

        # Pass the extra context into submit()
        return await submit(info, extra_context=extra_context)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
