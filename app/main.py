import os, io, json, shutil
from typing import Optional, List, Literal, Dict, Any
from fastapi import FastAPI, HTTPException, Form
from pydantic import BaseModel
import httpx
import numpy as np
from datetime import datetime
from fme import ace
from fme.ace.config import load_config
from huggingface_hub import hf_hub_download

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Download checkpoints
os.makedirs("/app/checkpoints", exist_ok=True)
ckpt_path = "/app/checkpoints/ACE2-ERA5.ckpt"

if not os.path.exists(ckpt_path):
    print("⬇️ Downloading ACE2-ERA5 from Hugging Face…")
    hf_path = hf_hub_download(repo_id="allenai/ACE2-ERA5", filename="ACE2-ERA5.ckpt")
    shutil.copy(hf_path, ckpt_path)
    print("✅ Saved at", ckpt_path)
else:
    print("✅ ACE2-ERA5 checkpoint already available:", ckpt_path)

# config
emu_cfg = load_config("/app/configs/config-inference.yaml", config_type="inference")
emu = ace.Stepper.from_config(emu_cfg)


OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")


if not OPENAI_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable not set")
if not ANTHROPIC_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY environment variable not set")

app = FastAPI(title="RWAgent (ACE Edition)", version="1.0.0")


class Question(BaseModel):
    query: str
    time: Optional[str] = None
    region: Optional[str] = None
    variables: Optional[List[str]] = None
    prefer: Optional[Literal["openai","claude"]] = None
    need_layers: bool = True
    horizon_steps: int = 4

def choose_model(q: Question) -> Optional[str]:
    # User must explicitly select the model
    if q.prefer in ["openai", "claude"]:
        return q.prefer
    return None

async def call_openai(system_msg: str, user_msg: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_KEY}"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role":"system","content":system_msg},
                     {"role":"user","content":user_msg}],
        "temperature": 0.2
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

async def call_claude(system_msg: str, user_msg: str) -> str:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 1500,
        "temperature": 0.2,
        "system": system_msg,
        "messages": [{"role":"user","content":user_msg}]
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()["content"][0]["text"]

@app.post("/ask")
async def ask(q: Question):
    model_choice = choose_model(q)
    if not model_choice:
        raise HTTPException(status_code=400, detail="Please specify which model to use: 'openai' or 'claude'.")

    SYSTEM_PROMPT = "You are an environmental research assistant. Always include units and cite data sources."
    prompt = f"Question: {q.query}\nTime: {q.time}\nVariables: {q.variables}"

    # route to the correct LLM
    if model_choice == "openai":
        answer = await call_openai(SYSTEM_PROMPT, prompt)
    elif model_choice == "claude":
        answer = await call_claude(SYSTEM_PROMPT, prompt)
    else:
        raise HTTPException(status_code=400, detail="Invalid model choice.")

    return {"model": model_choice, "answer": answer}


@app.get("/health")
async def health():
    import httpx, os
    results = {}
    # Test OpenAI key
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"}
            )
            results["openai"] = "✅ OK" if r.status_code == 200 else f"❌ {r.status_code}"
    except Exception as e:
        results["openai"] = f"❌ {e}"

    # Test Claude key
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": os.getenv("ANTHROPIC_API_KEY"),
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-5-haiku-20241022",
                    "max_tokens": 5,
                    "messages": [{"role": "user", "content": "ping"}],
                },
            )
            results["claude"] = "✅ OK" if r.status_code == 200 else f"❌ {r.status_code}"
    except Exception as e:
        results["claude"] = f"❌ {e}"

    return results

@app.post("/forecast")
async def forecast(datetime_utc: str = Form(...), simulation_length: int = Form(4)):
    """
    Run climate forecast using AI2 Climate Emulator (ACE).
    """
    try:
        forecast = emu.forecast(
            init_time=datetime.fromisoformat(datetime_utc.replace("Z", "")),
            steps=simulation_length,
        )

        output_path = "/app/app/ace_forecast.npy"
        np.save(output_path, forecast)
        return {"status": "ok", "output_file": output_path, "shape": forecast.shape}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
