from fastapi import FastAPI
import openai
from utils.webhook import router as webhook_router
from utils.core import submit, StartupInfo

app = FastAPI()
app.include_router(webhook_router)

# Set your OpenAI API key here (or use environment variables)
openai.api_key = ""
