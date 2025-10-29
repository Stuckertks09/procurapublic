# agents/gateway_agent.py
import os
import asyncio
import threading
from datetime import datetime
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel

from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    StartSessionContent,
    TextContent,
)

# ------------------------------------------------------------------------------
# Config
# ------------------------------------------------------------------------------
ORCHESTRATOR_ADDR = os.getenv("ORCHESTRATOR_ADDR")
AGENT_MNEMONIC = os.getenv("AGENT_MNEMONIC")

# ------------------------------------------------------------------------------
# ✅ Create Gateway Agent (NO PORT, NO MAILBOX, NO PROTOCOL)
# ------------------------------------------------------------------------------
gateway = Agent(
    name="gateway_agent",
    seed=AGENT_MNEMONIC,
    mailbox=False,     # ✅ do not receive messages
    port=None,         # ✅ do not open socket
    endpoint=None,     # ✅ do not attempt registration endpoint
)

fund_agent_if_low(gateway.wallet.address())

# ------------------------------------------------------------------------------
# Async outbound queue
# ------------------------------------------------------------------------------
_outbox = asyncio.Queue()
_ready = asyncio.Event()

async def enqueue_chat(text: str, start: bool):
    """Push message onto agent-side queue."""
    await _ready.wait()
    await _outbox.put((start, text))

@gateway.on_event("startup")
async def startup(ctx: Context):
    _ready.set()

    async def worker():
        while True:
            start, text = await _outbox.get()

            if start:
                await ctx.send(ORCHESTRATOR_ADDR, ChatMessage(
                    timestamp=datetime.utcnow(),
                    msg_id=uuid4(),
                    content=[StartSessionContent(type="start-session")]
                ))

            await ctx.send(ORCHESTRATOR_ADDR, ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=text)]
            ))

    asyncio.create_task(worker())

def start_gateway():
    threading.Thread(target=gateway.run, daemon=True).start()

# ------------------------------------------------------------------------------
# 🌐 FastAPI API Layer (Render exposes this)
# ------------------------------------------------------------------------------
app = FastAPI(title="Gateway API")

class EnqueueBody(BaseModel):
    text: str
    start: bool = False

@app.post("/enqueue")
async def enqueue(body: EnqueueBody):
    await enqueue_chat(body.text, body.start)
    return {"queued": body.text, "start": body.start}

@app.on_event("startup")
async def app_start():
    start_gateway()
