from fastapi import FastAPI
import openai
from utils.webhook import router as webhook_router
from utils.core import submit, StartupInfo

app = FastAPI()
app.include_router(webhook_router)

# Set your OpenAI API key here (or use environment variables)
openai.api_key = os.getenv('OPENAI_API_KEY')

from utils.core import process_deal
process_deal(
    name="AcmeAI",
    email_to="you@gmail.com",
    prompt="Write a concise deal memo for AcmeAI..."
)
print("done")
