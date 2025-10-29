import os
import httpx
import random
import datetime
from typing import List

from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
from agents.messages import ProcurementRequest, LaptopResponse, LaptopOption

# ------------------------------------------------------------------------------
# ✅ Environment-driven configuration
# ------------------------------------------------------------------------------
PORT = int(os.getenv("PORT", "8000"))
PUBLIC_URL = os.getenv("PUBLIC_URL", f"http://127.0.0.1:{PORT}")
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:9000/api/laptops")
NOTIFY_URL = os.getenv("NOTIFY_URL", "http://127.0.0.1:9000/api/notify")
AGENT_MNEMONIC = os.getenv("AGENT_MNEMONIC")  # optional stable identity

# ------------------------------------------------------------------------------
# ✅ Agent Setup
# ------------------------------------------------------------------------------
scout = Agent(
    name="scout_agent",
    port=PORT,
    endpoint=f"{PUBLIC_URL}/submit",
    mailbox=True,
    seed=AGENT_MNEMONIC,
)

proto = Protocol(name="scout_protocol")


# ------------------------------------------------------------------------------
# ✅ SSE Notify Helper
# ------------------------------------------------------------------------------
async def notify(request_id: str, message: str, done: bool = False, error: bool = False):
    """Send live updates to SSE gateway (safe, non-blocking)."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                NOTIFY_URL,
                json={"request_id": request_id, "message": message, "done": done, "error": error},
            )
    except Exception as e:
        print(f"[Scout Notify Error] {e}")


# ------------------------------------------------------------------------------
# ✅ Dataset Metadata Simulation (Ocean Protocol-style)
# ------------------------------------------------------------------------------
def generate_ocean_metadata():
    return {
        "data_source": "ocean-protocol",
        "datatoken_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "dataset_name": "Enterprise Laptop Suppliers Q4 2025",
        "access_type": "compute-to-data",
        "data_quality_score": round(random.uniform(0.85, 0.98), 2),
        "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
    }


# ------------------------------------------------------------------------------
# ✅ Procurement Handler
# ------------------------------------------------------------------------------
@proto.on_message(ProcurementRequest)
async def handle_procurement_request(ctx: Context, sender: str, msg: ProcurementRequest):
    print(f"\n🔍 [Scout] Received ProcurementRequest: {msg.request_id}")
    await notify(msg.request_id, f"🔍 Scout received procurement request (use_case={msg.use_case})")

    try:
        # Step 1 — Fetch dataset
        await notify(msg.request_id, "📡 Fetching dataset from Ocean Protocol (simulated)")
        async with httpx.AsyncClient() as client:
            response = await client.get(FASTAPI_URL)
            all_laptops = response.json().get("laptops", [])

        ocean_meta = generate_ocean_metadata()
        await notify(msg.request_id, f"📥 Retrieved {len(all_laptops)} laptops from dataset")

        # Step 2 — Apply business rules & requirements
        candidates: List[LaptopOption] = []
        for laptop_data in all_laptops:
            if msg.use_case not in laptop_data.get("use_cases", []):
                continue
            if msg.min_ram_gb and laptop_data["specs"]["ram_gb"] < msg.min_ram_gb:
                continue
            if msg.min_storage_gb and laptop_data["specs"]["storage_gb"] < msg.min_storage_gb:
                continue
            if msg.preferred_brand and laptop_data["brand"].lower() != msg.preferred_brand.lower():
                continue
            if laptop_data["stock"] < msg.quantity:
                continue
            if laptop_data["price"] > msg.max_budget_per_unit * 1.15:  # slight budget tolerance
                continue

            laptop_data["ocean_meta"] = ocean_meta
            candidates.append(LaptopOption(**laptop_data))

        print(f"✅ [Scout] Found {len(candidates)} matching candidates")
        await notify(msg.request_id, f"✅ Scout found {len(candidates)} matching candidates")

        # Step 3 — Reply to orchestrator
        await ctx.send(sender, LaptopResponse(request_id=msg.request_id, laptops=candidates))
        await notify(msg.request_id, "📤 Scout forwarded results to orchestrator")

    except Exception as e:
        print(f"❌ [Scout] Error: {e}")
        await notify(msg.request_id, f"❌ Scout encountered an error: {e}", error=True)
        await ctx.send(sender, LaptopResponse(request_id=msg.request_id, laptops=[]))


# ------------------------------------------------------------------------------
# ✅ Init + Register
# ------------------------------------------------------------------------------
fund_agent_if_low(scout.wallet.address())
scout.include(proto, publish_manifest=True)

if __name__ == "__main__":
    print("🔍 Starting Scout Agent (Ocean-Simulated Laptop Dataset)...")
    print("=" * 80)
    print(f"🌐 Endpoint: {PUBLIC_URL}/submit")
    print(f"📡 FASTAPI_URL: {FASTAPI_URL}")
    print(f"📢 NOTIFY_URL: {NOTIFY_URL}")
    print("=" * 80)
    scout.run()
