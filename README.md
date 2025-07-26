# VC Evaluator Tool

This is a backend tool built with FastAPI to automate venture capital deal memo generation. It takes startup submissions (e.g., via Typeform), uses GPT-4 to create a summary and a full deal memo PDF, sends them via email, and logs the submission to a Google Sheet.

## Features

- 🌐 FastAPI backend
- 🤖 GPT-4 powered memo generation
- 📩 Email delivery of summarized + full PDF memo
- 📊 Google Sheets logging
- 📁 Output folder for memo storage

## Requirements

- Python 3.9+
- Gmail App Password (not main password)
- OpenAI API Key (GPT-4)
- Google Sheets API credentials

## Setup

1. Clone the repo:
    ```bash
    git clone https://github.com/yourusername/VC-Evaluator.git
    cd VC-Evaluator
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Set your environment variables in `.env` or directly in `main.py`:
    - `OPENAI_API_KEY`
    - `GMAIL_SENDER`
    - `GMAIL_APP_PASSWORD`
    - `GOOGLE_SHEET_ID`
    - `ASSISTANT_ID`

4. Run the server:
    ```bash
    uvicorn main:app --reload
    ```

## Folder Structure

