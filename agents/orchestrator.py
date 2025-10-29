# agents/orchestrator.py — Orchestrator with SSE notify (parallel to chat)
from datetime import datetime
from uuid import uuid4
from typing import Dict, Optional
import os
import re
import httpx

from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low

# Chat protocol (uAgents core contrib)
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    StartSessionContent,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

from agents.messages import (
    ProcurementRequest, LaptopResponse,
    LaptopEvaluationRequest, LaptopEvaluationResult,
    BulkNegotiationRequest, BulkNegotiationResult,
    ScoredLaptop, LaptopScoredResponse
)

# -----------------------------------------------------------------------------
# ✅ Environment-driven configuration
# -----------------------------------------------------------------------------
PORT = int(os.getenv("AGENT_PORT", "8002"))
PUBLIC_URL = os.getenv("PUBLIC_URL", f"http://127.0.0.1:{PORT}")  # e.g., https://orchestrator.onrender.com
NOTIFY_URL = os.getenv("NOTIFY_URL", "http://127.0.0.1:9000/api/notify")
AGENT_MNEMONIC = os.getenv("AGENT_MNEMONIC")  # optional stable identity/seed

# Downstream agent addresses (Agentverse/ASI on-chain addresses)
SCOUT_ADDR   = os.getenv("SCOUT_ADDR", "agent1qtn4ckex9l5ytkee37k55yzcemtpt0svhktxty4q0kkaexx8g8xlwpll9sf")
COMPUTE_ADDR = os.getenv("COMPUTE_ADDR", "agent1q04u5agrk4xj3au80avzn208j4g4f4km6662wqnv26qy026rj7kfy654fjn")
EVAL_ADDR    = os.getenv("EVAL_ADDR",  "agent1qd24yq6av5wchue0n6pw2ht9qg95l0vl0y35nyajsxha5juhdvyrz2ae62x")
NEGO_ADDR    = os.getenv("NEGO_ADDR",  "agent1q2hsweq7l3004gejs63f3lve4zseha54ay7n9lj68c3zev2vtnlaxchak47")

# -----------------------------------------------------------------------------
# ✅ SSE notify (safe if gateway not running)
# -----------------------------------------------------------------------------
async def notify(request_id: str, message: str, *, done: bool = False, error: bool = False):
    """Fire-and-forget log line to the SSE gateway."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
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
        print(f"[Orchestrator Notify Error] {e}")

# -----------------------------------------------------------------------------
# ✅ Agent
# -----------------------------------------------------------------------------
orchestrator = Agent(
    name="orchestrator_agent",
    port=PORT,
    endpoint=f"{PUBLIC_URL}/submit",
    mailbox=True,
    seed=AGENT_MNEMONIC,
)

chat_proto = Protocol(spec=chat_protocol_spec)
wire_proto = Protocol(name="wire")

# -----------------------------------------------------------------------------
# ✅ Utilities
# -----------------------------------------------------------------------------
def mk_text_chat(text: str) -> ChatMessage:
    """Wrap plain text into a ChatMessage."""
    content = [TextContent(type="text", text=text)]
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )

def extract_req_id_from_text(text: str) -> Optional[str]:
    """
    Optional SSE correlation: if chat text contains 'REQID:<uuid>' we use it.
    Example: 'REQID:9d7... I need 10 laptops ...'
    """
    m = re.search(r"REQID:([0-9a-fA-F-]{8,36})", text)
    return m.group(1) if m else None

# Per-request state (minimal orchestration memory)
STATE: Dict[str, Dict] = {}

def parse_user_requirements(text: str) -> dict:
    """
    Parse user input to extract laptop requirements.
    """
    text_lower = text.lower()

    # Quantity
    quantity = 10  # default
    qty_match = re.search(r'(\d+)\s+laptop', text_lower)
    if qty_match:
        quantity = int(qty_match.group(1))

    # Budget
    budget = 1500.0  # default
    budget_match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', text)
    if budget_match:
        budget = float(budget_match.group(1).replace(',', ''))
    elif 'under' in text_lower:
        under_match = re.search(r'under\s+(\d+)', text_lower)
        if under_match:
            budget = float(under_match.group(1))

    # Use case
    use_case = "office-work"
    if any(word in text_lower for word in ['video', 'editing', 'photo', 'creative', 'design']):
        use_case = "video-editing"
    elif any(word in text_lower for word in ['programming', 'coding', 'development', 'dev']):
        use_case = "programming"
    elif any(word in text_lower for word in ['data', 'science', 'ml', 'machine learning', 'ai']):
        use_case = "data-science"
    elif any(word in text_lower for word in ['gaming', 'game']):
        use_case = "gaming"

    # RAM
    min_ram = None
    ram_match = re.search(r'(\d+)\s*gb\s+ram', text_lower)
    if ram_match:
        min_ram = int(ram_match.group(1))
    elif 'video' in text_lower or 'programming' in text_lower:
        min_ram = 16

    # Storage
    min_storage = None
    storage_match = re.search(r'(\d+)\s*gb\s+(?:storage|ssd)', text_lower)
    if storage_match:
        min_storage = int(storage_match.group(1))

    # Brand
    preferred_brand = None
    brands = ['dell', 'lenovo', 'hp', 'asus', 'acer', 'apple', 'msi']
    for brand in brands:
        if brand in text_lower:
            preferred_brand = brand
            break

    # Cost vs performance
    prefer_performance = True
    if any(word in text_lower for word in ['cheap', 'budget', 'affordable', 'cost']):
        prefer_performance = False
    elif any(word in text_lower for word in ['high-end', 'powerful', 'performance', 'fast']):
        prefer_performance = True

    return {
        'quantity': quantity,
        'budget': budget,
        'use_case': use_case,
        'min_ram': min_ram,
        'min_storage': min_storage,
        'preferred_brand': preferred_brand,
        'prefer_performance': prefer_performance
    }

# -----------------------------------------------------------------------------
# ✅ Startup Event
# -----------------------------------------------------------------------------
@orchestrator.on_event("startup")
async def startup(ctx: Context):
    print("\n" + "🚀" * 40)
    print("LAPTOP PROCUREMENT ORCHESTRATOR STARTED!")
    print(f"Agent Address: {ctx.agent.address}")
    print(f"Agent Name: {ctx.agent.name}")
    print(f"Listening on port: {PORT}")
    print(f"Endpoint: {PUBLIC_URL}/submit")
    print(f"Mailbox: ENABLED")
    print("Downstream addresses:")
    print(f"  • SCOUT_ADDR   = {SCOUT_ADDR}")
    print(f"  • COMPUTE_ADDR = {COMPUTE_ADDR}")
    print(f"  • EVAL_ADDR    = {EVAL_ADDR}")
    print(f"  • NEGO_ADDR    = {NEGO_ADDR}")
    print("🔔 NOTIFY_URL:", NOTIFY_URL)
    print("🚀" * 40 + "\n")
    ctx.logger.info("Orchestrator ready for laptop procurement requests")

# -----------------------------------------------------------------------------
# ✅ Chat Protocol Handlers
# -----------------------------------------------------------------------------
HELP_MESSAGE = (
    "🤖 I need a bit more detail to process your request.\n\n"
    "I look for **3 key things**:\n"
    "1) **How many** laptops\n"
    "2) **What they're used for** (video editing, programming, travel, etc.)\n"
    "3) **Your max budget per unit**\n\n"
    "**Try:**\n"
    "• *I need 10 laptops for video editing under $1500 each*\n"
    "• *Find me 5 programming laptops with 16GB RAM*\n"
)

GENERIC_GREETINGS = {"hello", "hi", "hey", "yo", "hola", "sup", "what's up"}


@chat_proto.on_message(ChatMessage)
async def on_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    print("\n" + "=" * 80)
    print("💬 CHAT MESSAGE RECEIVED")
    print(f"From: {sender}")
    print(f"Message ID: {msg.msg_id}")
    print("=" * 80)

    # Acknowledge receipt
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.utcnow(),
        acknowledged_msg_id=msg.msg_id
    ))
    print("✅ Acknowledgement sent")

    for item in msg.content:

        # Session Start
        if isinstance(item, StartSessionContent):
            await ctx.send(sender, mk_text_chat(
                "👋 Welcome to ASI Laptop Procurement!\n\n"
                + HELP_MESSAGE
            ))
            continue

        # Session End
        if isinstance(item, EndSessionContent):
            await ctx.send(sender, mk_text_chat("👋 Session closed. See you next time!"))
            continue

        # Text Handling
        if isinstance(item, TextContent):
            user_text = (item.text or "").strip()
            if not user_text:
                continue

            # Handle simple greetings / low-info messages
            if user_text.lower() in GENERIC_GREETINGS or len(user_text.split()) < 3:
                await ctx.send(sender, mk_text_chat(HELP_MESSAGE))
                continue

            incoming_req_id = extract_req_id_from_text(user_text)
            request_id = incoming_req_id or str(uuid4())

            try:
                # Parse user request
                requirements = parse_user_requirements(user_text)
                STATE[request_id] = {"user": sender, "requirements": requirements}

                # Notify UI (SSE)
                await notify(request_id, "✅ Request accepted by Orchestrator")
                await notify(
                    request_id,
                    f"• use_case={requirements['use_case']} | qty={requirements['quantity']} | budget=${requirements['budget']}"
                )
                if incoming_req_id:
                    await notify(request_id, "🔗 Correlated to frontend stream via REQID token")

                # Build request for Scout agent
                procurement_req = ProcurementRequest(
                    request_id=request_id,
                    use_case=requirements['use_case'],
                    quantity=requirements['quantity'],
                    max_budget_per_unit=requirements['budget'],
                    min_ram_gb=requirements['min_ram'],
                    min_storage_gb=requirements['min_storage'],
                    preferred_brand=requirements['preferred_brand'],
                    prefer_performance=requirements['prefer_performance']
                )

                # UX feedback
                await ctx.send(sender, mk_text_chat(
                    f"🔍 Searching for laptops...\n"
                    f"Use Case: {requirements['use_case']}\n"
                    f"Quantity: {requirements['quantity']}\n"
                    f"Budget: ${requirements['budget']}/unit\n"
                    f"⏳ Analyzing options..."
                ))
                await notify(request_id, "🧭 Dispatching Scout to filter the catalog…")

                # Send to Scout
                print("📤 Sending ProcurementRequest to Scout")
                await ctx.send(SCOUT_ADDR, procurement_req)
                print("✅ Request sent to Scout")

            except Exception as e:
                # Parsing failed → Send user help
                await ctx.send(sender, mk_text_chat(HELP_MESSAGE))
                rid = incoming_req_id or "unknown"
                await notify(rid, f"❌ Failed to parse input: {e}", error=True)


@chat_proto.on_message(ChatAcknowledgement)
async def on_chat_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    print(f"✅ ACK received from {sender}")


@chat_proto.on_message(ChatAcknowledgement)
async def on_chat_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    print(f"✅ ACK received from {sender}")

# -----------------------------------------------------------------------------
# ✅ Wire Protocol: Inter-Agent Communication
# -----------------------------------------------------------------------------
@wire_proto.on_message(LaptopResponse)
async def on_laptop_response(ctx: Context, sender: str, msg: LaptopResponse):
    print(f"\n💻 Received LaptopResponse (Scout)")
    st = STATE.get(msg.request_id, {})
    user = st.get("user")
    requirements = st.get("requirements", {})

    if not msg.laptops:
        if user:
            await ctx.send(user, mk_text_chat("❌ No laptops found matching your criteria."))
        await notify(msg.request_id, "❌ Scout found 0 candidates — stopping.", error=True)
        return

    st["laptops"] = msg.laptops
    STATE[msg.request_id] = st

    await notify(msg.request_id, f"📦 Scout Agent found {len(msg.laptops)} candidates from OCEAN data (mocked). Forwarding to Compute…")
    if user:
        await ctx.send(user, mk_text_chat(
            f"📦 Scout found {len(msg.laptops)} candidates. Forwarding to ComputeAgent for CUDOS scoring (mocked)..."
        ))

    print(f"📤 Forwarding to ComputeAgent for CUDOS scoring")
    await ctx.send(COMPUTE_ADDR, LaptopEvaluationRequest(
        request_id=msg.request_id,
        laptops=msg.laptops,
        use_case=requirements.get('use_case', 'office-work'),
        quantity=requirements.get('quantity', 10),
        max_budget=requirements.get('budget', 1500.0),
        prefer_performance=requirements.get('prefer_performance', True)
    ))
    print("✅ Sent to ComputeAgent")

@wire_proto.on_message(LaptopScoredResponse)
async def on_scored_laptops(ctx: Context, sender: str, msg: LaptopScoredResponse):
    print(f"\n📈 Received LaptopScoredResponse (ComputeAgent)")
    st = STATE.get(msg.request_id, {})
    requirements = st.get("requirements", {})
    user = st.get("user")

    if not msg.laptops:
        if user:
            await ctx.send(user, mk_text_chat("❌ No viable laptops after compute scoring."))
        await notify(msg.request_id, "❌ Compute returned empty results — stopping.", error=True)
        return

    await notify(msg.request_id, "⚙️ Compute scoring complete (processor/warranty/shipping). Sending to MeTTa…")
    if user:
        await ctx.send(user, mk_text_chat("🧠 Scores computed! Sending to MeTTa-based evaluation agent..."))

    print(f"📤 Forwarding to Evaluator for MeTTa reasoning")
    await ctx.send(EVAL_ADDR, LaptopEvaluationRequest(
        request_id=msg.request_id,
        scored_laptops=msg.laptops,  # pass full ScoredLaptopOption objects
        use_case=requirements['use_case'],
        quantity=requirements['quantity'],
        max_budget=requirements['budget'],
        prefer_performance=requirements['prefer_performance']
    ))
    print("✅ Sent to Evaluator")

@wire_proto.on_message(LaptopEvaluationResult)
async def on_eval_result(ctx: Context, sender: str, msg: LaptopEvaluationResult):
    print(f"\n📊 Received LaptopEvaluationResult")
    st = STATE.get(msg.request_id, {})
    st["ranked"] = msg.ranked
    STATE[msg.request_id] = st

    # Notify hybrid breakdown (top 3)
    await notify(msg.request_id, "🧩 Hybrid evaluation ready (MeTTa ⊕ Compute ⊕ Value). Top 3:")
    for i, sl in enumerate(msg.ranked[:3], 1):
        metta_used = "metta" in (sl.rationale or "").lower()
        line = (
            f"   {i}. {sl.laptop.model} → "
            f"symbolic={getattr(sl, 'symbolic_score', 0):.3f}, "
            f"compute={getattr(sl, 'compute_score', 0):.3f}, "
            f"value={getattr(sl, 'value_score', 0):.3f} "
            f"→ final={sl.score:.3f} "
            f"| {'MeTTa✓' if metta_used else 'fallback'}"
        )
        await notify(msg.request_id, line)

    user = st.get("user")
    requirements = st.get("requirements", {})

    if not msg.ranked:
        if user:
            await ctx.send(user, mk_text_chat("❌ No suitable laptops found."))
        await notify(msg.request_id, "❌ No suitable options after evaluation.", error=True)
        return

    top: ScoredLaptop = msg.ranked[0]

    if user:
        top3_summary = "Metta Evaulation Complete! Hybrid scored between compute, value, and symbolic scores and found 🏆 **Top 3 Laptops:**\n\n"
        for i, sl in enumerate(msg.ranked[:3], 1):
            top3_summary += (
                f"{i}. **{sl.laptop.model}** by {sl.laptop.brand}\n"
                f"   • Price: ${sl.laptop.price}\n"
                f"   • Score: {sl.score:.3f}\n"
                f"   • {sl.laptop.specs.processor}, {sl.laptop.specs.ram_gb}GB RAM\n"
                f"   • {sl.laptop.rating}⭐ ({sl.laptop.review_count} reviews)\n\n"
            )
        top3_summary += "🤝 Sending top choice to Negotiating Agent for better pricing..."
        await ctx.send(user, mk_text_chat(top3_summary))

    await notify(msg.request_id, f"🤝 Sending top choice to Negotiator: {top.laptop.model}")

    print(f"📤 Sending to Negotiator")
    await ctx.send(NEGO_ADDR, BulkNegotiationRequest(
        request_id=msg.request_id,
        top_pick=top,
        quantity=requirements.get('quantity', 10),
        target_price_per_unit=requirements.get('budget')
    ))
    print("✅ Sent to Negotiator")

@wire_proto.on_message(BulkNegotiationResult)
async def on_nego_result(ctx: Context, sender: str, msg: BulkNegotiationResult):
    print(f"\n🤝 Received BulkNegotiationResult")
    st = STATE.get(msg.request_id, {})
    user = st.get("user")
    ranked = st.get("ranked", [])
    requirements = st.get("requirements", {})

    if not user or not ranked:
        print("❌ Missing state")
        await notify(msg.request_id, "❌ Missing state on negotiation return.", error=True)
        return

    top = ranked[0]

    if msg.accepted:
        summary = (
            f"✅ **DEAL SECURED!**\n\n"
            f"**Selected:** {top.laptop.model} by {top.laptop.brand}\n\n"
            f"**Specs:**\n"
            f"• Processor: {top.laptop.specs.processor}\n"
            f"• RAM: {top.laptop.specs.ram_gb}GB\n"
            f"• Storage: {top.laptop.specs.storage_gb}GB\n"
            f"• GPU: {top.laptop.specs.gpu}\n"
            f"• Screen: {top.laptop.specs.screen_size}\"\n\n"
            f"**Pricing:**\n"
            f"• Original: ${msg.original_price:.2f}/unit\n"
            f"• Discount: {msg.discount_applied_pct}%\n"
            f"• Final Price: ${msg.final_price_per_unit:.2f}/unit\n"
            f"• Quantity: {requirements.get('quantity', 10)} units\n"
            f"• Total: ${msg.total_cost:.2f}\n"
            f"• 💰 You Save: ${msg.savings:.2f}**\n\n"
            f"**Details:**\n"
            f"• Rating: {top.laptop.rating}⭐ ({top.laptop.review_count} reviews)\n"
            f"• Warranty: {top.laptop.warranty_years} years\n"
            f"• Shipping: {top.laptop.shipping_days} days\n"
            f"• Supplier: {top.laptop.supplier}\n\n"
            f"**Why this choice?**\n"
            f"MeTTa symbolic reasoning weighted performance ({top.laptop.specs.ram_gb}GB RAM) "
            f"against value ({msg.discount_applied_pct}% discount) and reviews ({top.laptop.rating}★) "
            f"to optimize for your ({requirements.get('use_case', 'general')}) use case."
        )
        await notify(
            msg.request_id,
            f"🎯 Deal secured: {top.laptop.model} at ${msg.final_price_per_unit:.2f}/unit "
            f"(discount {msg.discount_applied_pct}%). Total ${msg.total_cost:.2f}.",
            done=True
        )
    else:
        summary = (
            f"⚠️ **NEGOTIATION FAILED**\n\n"
            f"Could not secure **{top.laptop.model}** within budget.\n"
            f"Reason: {msg.note}\n\n"
            f"Would you like to:\n"
            f"• Consider the next option?\n"
            f"• Adjust your budget?\n"
            f"• Change requirements?"
        )
        await notify(msg.request_id, f"❌ Negotiation failed: {msg.note}", error=True)

    await ctx.send(user, mk_text_chat(summary))
    print("✅ Final result sent to user")

# -----------------------------------------------------------------------------
# ✅ Register & Run
# -----------------------------------------------------------------------------
fund_agent_if_low(orchestrator.wallet.address())
orchestrator.include(chat_proto, publish_manifest=True)
orchestrator.include(wire_proto, publish_manifest=True)

if __name__ == "__main__":
    print("\n🎬 Starting Laptop Procurement Orchestrator...")
    print("=" * 80)
    print(f"🌐 Endpoint: {PUBLIC_URL}/submit")
    print(f"🔔 NOTIFY_URL: {NOTIFY_URL}")
    print("Downstream agent addresses:")
    print(f"  • SCOUT_ADDR   = {SCOUT_ADDR}")
    print(f"  • COMPUTE_ADDR = {COMPUTE_ADDR}")
    print(f"  • EVAL_ADDR    = {EVAL_ADDR}")
    print(f"  • NEGO_ADDR    = {NEGO_ADDR}")
    print("=" * 80)
    orchestrator.run()
