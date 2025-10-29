# agents/compute_agent.py — CUDOS compute simulation + live notify (env-ready)

import os
import httpx
import datetime
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
from agents.messages import LaptopEvaluationRequest, LaptopScoredResponse, ScoredLaptopOption

# ------------------------------------------------------------------------------
# Environment-based configuration (✅ Now ready for microservice deployment)
# ------------------------------------------------------------------------------

PORT = int(os.getenv("AGENT_PORT", "8004"))
PUBLIC_URL = os.getenv("PUBLIC_URL", f"http://127.0.0.1:{PORT}")
SCORING_URL = os.getenv("SCORING_URL", "http://127.0.0.1:9000/api/score")
NOTIFY_URL = os.getenv("NOTIFY_URL", "http://127.0.0.1:9000/api/notify")

# Optional mnemonic for stable agent addresses
AGENT_MNEMONIC = os.getenv("AGENT_MNEMONIC")

# ------------------------------------------------------------------------------
# Agent Setup
# ------------------------------------------------------------------------------

compute_agent = Agent(
    name="compute_agent",
    port=PORT,
    endpoint=f"{PUBLIC_URL}/submit",   # ✅ dynamic endpoint
    mailbox=True,
    seed=AGENT_MNEMONIC                # ✅ optional stable identity support
)

proto = Protocol(name="compute_protocol")


# ------------------------------------------------------------------------------
# Notify helper — unchanged logic, now using dynamic NOTIFY_URL
# ------------------------------------------------------------------------------

async def notify(request_id: str, message: str, done: bool = False, error: bool = False):
    """Send a streaming update to the frontend via SSE gateway."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(NOTIFY_URL, json={
                "request_id": request_id,
                "message": message,
                "done": done,
                "error": error
            })
    except Exception as e:
        print(f"[Compute Notify Error] {e}")


# ------------------------------------------------------------------------------
# Message handler — unchanged behavior
# ------------------------------------------------------------------------------

@proto.on_message(LaptopEvaluationRequest)
async def handle_laptop_eval_request(ctx: Context, sender: str, msg: LaptopEvaluationRequest):
    print(f"\n🧮 [Compute] Received laptops for scoring (Request {msg.request_id})")
    await notify(msg.request_id, "🧮 Dispatching batch to CUDOS compute cluster...")

    try:
        # Prepare data payload
        laptop_dicts = [laptop.dict() for laptop in msg.laptops]
        await notify(msg.request_id, f"📦 {len(laptop_dicts)} laptops queued for evaluation...")

        async with httpx.AsyncClient() as client:
            response = await client.post(SCORING_URL, json={"laptops": laptop_dicts})
            scoring_data = response.json()

        await notify(
            msg.request_id,
            f"✅ CUDOS job completed: {scoring_data['compute_job_id']} "
            f"({scoring_data['execution_time_ms']} ms, cost {scoring_data['compute_cost']})"
        )

        # Add simulated compute metadata
        cudos_meta = {
            "compute_job_id": scoring_data["compute_job_id"],
            "network": "cudos-mainnet",
            "compute_cost": scoring_data["compute_cost"],
            "execution_time_ms": scoring_data["execution_time_ms"],
            "node_location": scoring_data["node_location"]
        }

        scored_laptops = []
        for result in scoring_data["results"]:
            base = next(l for l in msg.laptops if l.id == result["id"])
            await notify(
                msg.request_id,
                f"📊 {base.model}: proc={result['processor_score']} | "
                f"warr={result['warranty_score']} | ship={result['shipping_score']}"
            )
            scored_laptops.append(ScoredLaptopOption(
                base=base,
                processor_score=result["processor_score"],
                warranty_score=result["warranty_score"],
                shipping_score=result["shipping_score"],
                cudos_meta=cudos_meta
            ))

        await ctx.send(sender, LaptopScoredResponse(
            request_id=msg.request_id,
            laptops=scored_laptops
        ))

        await notify(msg.request_id, "✅ Compute scoring complete — forwarding to Evaluator...")

        print(f"✅ [Compute] Sent scored results back to orchestrator")

    except Exception as e:
        error_msg = f"❌ [Compute] Error scoring laptops: {e}"
        print(error_msg)
        await notify(msg.request_id, error_msg, error=True)


# ------------------------------------------------------------------------------
# Bootstrap
# ------------------------------------------------------------------------------

fund_agent_if_low(compute_agent.wallet.address())
compute_agent.include(proto, publish_manifest=True)

if __name__ == "__main__":
    print("🧮 Starting Compute Agent (CUDOS Simulation)...")
    print("PORT:", PORT)
    print("PUBLIC_URL:", PUBLIC_URL)
    print("SCORING_URL:", SCORING_URL)
    print("NOTIFY_URL:", NOTIFY_URL)
    print("=" * 80)
    compute_agent.run()
