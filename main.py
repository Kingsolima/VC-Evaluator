from fastapi import FastAPI
from utils.webhook import router as webhook_router  # <-- file must be utils/webhook.py

app = FastAPI()

@app.get("/")
def health():
    return {"status": "ok"}

# Mount webhook routes under /webhook/*
app.include_router(webhook_router, prefix="/webhook")
