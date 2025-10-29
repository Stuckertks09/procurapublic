# backend/main.py

import asyncio
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from uuid import uuid4

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# -----------------------------------------------------------------------------
# 🌐 Env Config
# -----------------------------------------------------------------------------
PORT = int(os.getenv("PORT", "9000"))
AUTO_START_ORCHESTRATION = True
GATEWAY_ENQUEUE_URL = os.getenv("GATEWAY_ENQUEUE_URL", "http://127.0.0.1:9000/enqueue")


# -----------------------------------------------------------------------------
# 🚀 FastAPI App
# -----------------------------------------------------------------------------
app = FastAPI(title="Procura Backend", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://pronet-0u6p.onrender.com",
        "*",   # ← ok during testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# 📡 SSE Infra
# -----------------------------------------------------------------------------
EVENT_QUEUES: Dict[str, asyncio.Queue] = {}
ACTIVE_IDS = set()

def _ensure_queue(req_id: str) -> asyncio.Queue:
    if req_id not in EVENT_QUEUES:
        EVENT_QUEUES[req_id] = asyncio.Queue()
        ACTIVE_IDS.add(req_id)
    return EVENT_QUEUES[req_id]

async def push_event(req_id: str, line: str):
    await _ensure_queue(req_id).put(f"[{datetime.utcnow().isoformat()}Z] {line}")

async def close_stream(req_id: str):
    await _ensure_queue(req_id).put("__STREAM_EOF__")

async def sse_iter(req_id: str):
    await push_event(req_id, "🔌 Stream connected")
    q = _ensure_queue(req_id)
    while True:
        line = await q.get()
        if line == "__STREAM_EOF__":
            yield "data: [STREAM CLOSED]\n\n"
            break
        yield f"data: {line}\n\n"

# -----------------------------------------------------------------------------
# 📦 Request Models
# -----------------------------------------------------------------------------
class ProcurementRequestBody(BaseModel):
    use_case: str
    quantity: int
    max_budget_per_unit: float
    min_ram_gb: Optional[int] = None
    min_storage_gb: Optional[int] = None
    preferred_brand: Optional[str] = None
    prefer_performance: bool = True

class NotifyBody(BaseModel):
    request_id: str
    message: str
    done: bool = False
    error: bool = False


# -----------------------------------------------------------------------------
# 🧠 Helper: Format chat text
# -----------------------------------------------------------------------------
def _build_user_text(body: ProcurementRequestBody, req_id: str):
    uc = body.use_case.replace("-", " ")
    text = f"REQID:{req_id} I need {body.quantity} laptops for {uc} under ${int(body.max_budget_per_unit)} each"
    if body.min_ram_gb:
        text += f" with {body.min_ram_gb}GB RAM"
    if body.min_storage_gb:
        text += f" and {body.min_storage_gb}GB storage"
    if body.preferred_brand:
        text += f" (brand: {body.preferred_brand})"
    return text


# -----------------------------------------------------------------------------
# 📨 Kickoff (Now Sends to Gateway via HTTP!)
# -----------------------------------------------------------------------------
@app.post("/api/procure")
async def api_procure(body: ProcurementRequestBody):
    req_id = str(uuid4())
    _ensure_queue(req_id)

    await push_event(req_id, "✅ Request accepted")

    if AUTO_START_ORCHESTRATION:
        await push_event(req_id, "🚀 Dispatching to Gateway...")
        text = _build_user_text(body, req_id)

        async def _kick():
            try:
                async with httpx.AsyncClient(timeout=8) as client:
                    await client.post(GATEWAY_ENQUEUE_URL, json={"text": "", "start": True})
                    await client.post(GATEWAY_ENQUEUE_URL, json={"text": text, "start": False})
                await push_event(req_id, "📨 Chat sent to orchestrator")
            except Exception as e:
                await push_event(req_id, f"⚠️ Gateway dispatch failed: {e}")

        asyncio.create_task(_kick())

    return {"request_id": req_id}


# -----------------------------------------------------------------------------
# 📢 Notify from Agents
# -----------------------------------------------------------------------------
@app.post("/api/notify")
async def api_notify(body: NotifyBody):
    await push_event(body.request_id, body.message)
    if body.done or body.error:
        await close_stream(body.request_id)
    return {"ok": True}


# -----------------------------------------------------------------------------
# 📺 SSE Stream
# -----------------------------------------------------------------------------
@app.get("/api/stream/{request_id}")
async def api_stream(request_id: str, request: Request):
    _ensure_queue(request_id)
    return StreamingResponse(sse_iter(request_id), headers={
        "Cache-Control": "no-cache",
        "Content-Type": "text/event-stream",
        "Access-Control-Allow-Origin": "*",
    })

# -----------------------------------------------------------------------------
# 💾 Data Serving (for Scout & Compute)
# -----------------------------------------------------------------------------
LAPTOPS_FILE = Path(__file__).parent.parent / "data" / "laptops.json"
with open(LAPTOPS_FILE, "r") as f:
    LAPTOPS = __import__("json").load(f).get("laptops", [])

SCORING_FILE = Path(__file__).parent.parent / "data" / "scoring_factors.json"
with open(SCORING_FILE, "r") as f:
    SCORING_FACTORS = __import__("json").load(f)


@app.get("/api/laptops")
def get_laptops():
    return {"laptops": LAPTOPS}


@app.post("/api/score")
def score_laptops(payload: dict):
    laptops = payload.get("laptops", [])
    scored = []
    max_warranty = SCORING_FACTORS["max_warranty_years"]
    max_shipping = SCORING_FACTORS["max_shipping_days"]

    for laptop in laptops:
        processor = laptop["specs"]["processor"]
        warranty = laptop["warranty_years"]
        shipping_days = laptop["shipping_days"]

        proc_score = 0.7
        for key, val in SCORING_FACTORS["processor_weights"].items():
            if key.lower() in processor.lower():
                proc_score = val
                break

        warranty_score = min(warranty / max_warranty, 1.0)
        shipping_score = round((max_shipping - shipping_days) / max_shipping, 2)

        scored.append({
            "id": laptop["id"],
            "processor_score": proc_score,
            "warranty_score": warranty_score,
            "shipping_score": shipping_score,
        })

    return {
        "compute_job_id": f"cudos-job-{random.randint(1000,9999)}",
        "execution_time_ms": random.randint(100, 300),
        "compute_cost": f"{round(random.uniform(0.001, 0.01), 4)} CUDOS",
        "node_location": "us-east-distributed-cluster",
        "results": scored,
    }
