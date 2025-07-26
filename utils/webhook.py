# utils/webhook.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
from utils.core import submit, StartupInfo

router = APIRouter()

class TypeformSubmission(BaseModel):
    form_response: Dict

def extract_answers(form_response: Dict) -> Dict:
    answers = {}
    for answer in form_response.get("answers", []):
        question = answer.get("field", {}).get("title", "Unknown Question")
        response = (
            answer.get("text")
            or answer.get("email")
            or answer.get("number")
            or str(answer)
        )
        answers[question] = response
    return answers

@router.post("/typeform-webhook")
async def typeform_webhook(submission: TypeformSubmission):
    try:
        answers = extract_answers(submission.form_response)

        info = StartupInfo(
            name=answers.get("Startup Name", "NA"),
            website=answers.get("Website", "NA"),
            round=answers.get("Funding Round", "NA"),
            investors=answers.get("Investors", "NA"),
            traction=answers.get("Traction", "NA"),
            team=answers.get("Team", "NA"),
            product=answers.get("Product", "NA"),
            email_to="yourgp@email.com"
        )

        return await submit(info)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
