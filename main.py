from fastapi import FastAPI
from utils.webhook import router as webhook_router

app = FastAPI()
app.include_router(webhook_router, prefix="/webhook")  # gives /webhook/typeform-webhook

@app.get("/")
def health():
    return {"status": "ok"}
