"""Japan Life Navigator — minimal test server."""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

app = FastAPI()

VB_API_KEY = os.environ["VOCAL_BRIDGE_API_KEY"]
VB_URL = "https://vocalbridgeai.com"

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/api/voice-token")
def voice_token():
    resp = requests.post(
        f"{VB_URL}/api/v1/token",
        headers={"X-API-Key": VB_API_KEY, "Content-Type": "application/json"},
        json={"participant_name": "Web User"},
        timeout=15,
    )
    if not resp.ok:
        return JSONResponse({"error": resp.text}, status_code=resp.status_code)
    return resp.json()
