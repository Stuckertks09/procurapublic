# agents/negotiator_agent.py — Bulk negotiator with env-based endpoint config

import os
import httpx
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
from agents.messages import BulkNegotiationRequest, BulkNegotiationResult

# ------------------------------------------------------------------------------
# ✅ Environment-driven configuration
# ------------------------------------------------------------------------------
PORT = int(os.getenv("AGENT_PORT", "8003"))
PUBLIC_URL = os.getenv("PUBLIC_URL", f"http://127.0.0.1:{PORT}")
NOTIFY_URL = os.getenv("NOTIFY_URL", "http://127.0.0.1:9000/api/notify")
AGENT_MNEMONIC = os.getenv("AGENT_MNEMONIC")  # optional stable wallet seed

# ------------------------------------------------------------------------------
# ✅ Agent Setup (uses dynamic endpoint)
# ------------------------------------------------------------------------------
negotiator = Agent(
    name="negotiator_agent",
    port=PORT,
    endpoint=f"{PUBLIC_URL}/submit",
    mailbox=True,
    seed=AGENT_MNEMONIC,
)

proto = Protocol(name="negotiator_protocol")


# ------------------------------------------------------------------------------
# ✅ SSE Notify Helper
# ------------------------------------------------------------------------------
async def notify(request_id: str, message: str, done: bool = False, error: bool = False):
    """Send streaming updates to frontend via SSE gateway."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                NOTIFY_URL,
                json={
                    "request_id": request_id,
                    "message": message,
                    "done": done,
                    "error": error,
                },
            )
    except Exception as e:
        print(f"[Negotiator Notify Error] {e}")


# ------------------------------------------------------------------------------
# ✅ Core Message Handler (unchanged logic)
# ------------------------------------------------------------------------------
@proto.on_message(BulkNegotiationRequest)
async def handle_negotiation(ctx: Context, sender: str, msg: BulkNegotiationRequest):
    print(f"\n🤝 [Negotiator] Received BulkNegotiationRequest!")
    print(f"   Request ID: {msg.request_id}")
    print(f"   Laptop: {msg.top_pick.laptop.model}")
    print(f"   Quantity: {msg.quantity}")
    print(f"   Original price: ${msg.top_pick.laptop.price}")

    await notify(msg.request_id, f"🤝 Negotiator evaluating bulk discount for {msg.quantity} units...")

    laptop = msg.top_pick.laptop
    original_price = laptop.price

    # ✅ Find applicable bulk discount tier
    discount_pct = 0.0
    for tier in sorted(laptop.bulk_pricing, key=lambda x: x.min_qty, reverse=True):
        if msg.quantity >= tier.min_qty:
            discount_pct = tier.discount_pct
            break

    final_price_per_unit = original_price * (1 - discount_pct / 100)
    total_cost = final_price_per_unit * msg.quantity
    savings = (original_price - final_price_per_unit) * msg.quantity

    # ✅ Check target price constraint
    accepted = True
    note = f"Applied {discount_pct}% bulk discount for {msg.quantity} units"
    if msg.target_price_per_unit and final_price_per_unit > msg.target_price_per_unit:
        accepted = False
        note = f"Final price ${final_price_per_unit:.2f} exceeds target ${msg.target_price_per_unit:.2f}"

    print(f"   💰 Discount: {discount_pct}%")
    print(f"   💵 Final price per unit: ${final_price_per_unit:.2f}")
    print(f"   💸 Total cost: ${total_cost:.2f}")
    print(f"   🎉 Savings: ${savings:.2f}")
    print(f"   Decision: {'✅ ACCEPTED' if accepted else '❌ REJECTED'}")

    # ✅ Frontend updates
    await notify(msg.request_id, f"💰 Discount tier: {discount_pct}%")
    await notify(msg.request_id, f"💵 Final price per unit: ${final_price_per_unit:.2f}")
    await notify(msg.request_id, f"💸 Total cost: ${total_cost:.2f}")
    await notify(msg.request_id, f"🎉 Savings: ${savings:.2f}")

    # ✅ Build response
    result = BulkNegotiationResult(
        request_id=msg.request_id,
        accepted=accepted,
        original_price=original_price,
        final_price_per_unit=final_price_per_unit,
        total_cost=total_cost,
        discount_applied_pct=discount_pct,
        savings=savings,
        note=note,
    )

    # ✅ Send result back to orchestrator
    await ctx.send(sender, result)
    await notify(msg.request_id, f"{'✅ Accepted' if accepted else '❌ Rejected'} - {note}", done=True)
    print(f"✅ Response sent!\n")


# ------------------------------------------------------------------------------
# ✅ Registration & Startup
# ------------------------------------------------------------------------------
fund_agent_if_low(negotiator.wallet.address())
negotiator.include(proto, publish_manifest=True)
negotiator.register()

if __name__ == "__main__":
    print("🤝 Starting Bulk Negotiator Agent...")
    print(f"PORT: {PORT}")
    print(f"PUBLIC_URL: {PUBLIC_URL}")
    print(f"NOTIFY_URL: {NOTIFY_URL}")
    print("=" * 80)
    negotiator.run()
