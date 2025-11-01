
# RWAgent (ACE Edition)

An intelligent research assistant combining **LLMs (OpenAI, Anthropic)** with the **AI2 Climate Emulator (ACE)** for high-resolution weather and climate forecasting.
Supports hybrid reasoning (language + simulation) and GPU acceleration on systems like the RTX 5090.

---

## Overview

RWAgent enables environmental forecasting and scientific querying by combining:

*  **LLMs (GPT-4o, Claude 3.5)** for reasoning, context understanding, and data interpretation.
*  **AI2 Climate Emulator (ACE / `fme`)** for fast neural weather forecasts.
*  **FastAPI backend** with Docker deployment.

---

##  Requirements

* **Docker + Docker Compose** (latest version)
* **NVIDIA GPU (recommended)** – e.g. RTX 5090 with CUDA drivers installed
* Environment variables:

  ```bash
  OPENAI_API_KEY=<your_openai_key>
  ANTHROPIC_API_KEY=<your_claude_key>
  ```

---

##  Build and Run

Clone the repo and build the containers:

```bash
docker compose down --remove-orphans
docker compose up --build
```

Once running, you’ll see:

```
Uvicorn running on http://0.0.0.0:8080
```

---

## Verify Installation

Check ACE is available:

```bash
docker compose exec api python -c "import fme; print(fme.__version__)"
```

If this prints a version (e.g. `0.4.1`), ACE is ready.

---

## LLM Health Check

Test both connected APIs:

```bash
curl http://localhost:8080/health
```

You should get:

```json
{
  "openai": "✅ OK",
  "claude": "✅ OK"
}
```

---

## Forecast Example (ACE)

Generate a short forecast using AI2’s `pangu_weather` model:

```bash
curl -X POST \
  -F "datetime_utc=2023-01-01T00:00:00Z" \
  -F "simulation_length=4" \
  http://localhost:8080/forecast
```

**Response:**

```json
{
  "status": "ok",
  "output_file": "/app/app/ace_forecast.npy",
  "shape": [1, 32, 720, 1440]
}
```

This saves an `ace_forecast.npy` file with predicted atmospheric data.

---

## Ask LLM

You can also ask reasoning or research questions:

```bash
curl -X POST "http://localhost:8080/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare temperature anomalies for 2024 and 2025",
    "prefer": "claude"
  }'
```

---

##  Project Structure

```
RWAgent/
├── app/
│   └── app/
│       ├── main.py            # FastAPI entrypoint
│       └── ace_forecast.npy   # Example forecast output
├── requirements.txt           # Dependencies (FastAPI, fme, etc.)
├── Dockerfile                 # Container build
└── docker-compose.yml         # Multi-service orchestration
```

---

##  Powered By

* [FastAPI](https://fastapi.tiangolo.com/)
* [AI2 Climate Emulator (ACE)](https://ai2-climate-emulator.readthedocs.io/)
* [OpenAI GPT-4o](https://platform.openai.com/)
* [Anthropic Claude 3.5](https://www.anthropic.com/)

