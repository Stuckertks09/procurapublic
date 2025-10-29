# agents/evaluator.py — Hybrid (MeTTa + Compute + Value) evaluation agent with env-based config

import os
from typing import List, Dict, Optional
import httpx

from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
from agents.messages import (
    LaptopEvaluationRequest,
    LaptopEvaluationResult,
    ScoredLaptop,
    ScoredLaptopOption,
    LaptopOption,
)

# ------------------------------------------------------------------------------
# ✅ Environment-based configuration (for microservice deployment)
# ------------------------------------------------------------------------------
PORT = int(os.getenv("AGENT_PORT", "8001"))
PUBLIC_URL = os.getenv("PUBLIC_URL", f"http://127.0.0.1:{PORT}")
NOTIFY_URL = os.getenv("NOTIFY_URL", "http://127.0.0.1:9000/api/notify")
AGENT_MNEMONIC = os.getenv("AGENT_MNEMONIC")  # optional stable identity


# ------------------------------------------------------------------------------
# ✅ Agent setup (dynamic endpoint + optional stable wallet)
# ------------------------------------------------------------------------------
evaluator = Agent(
    name="evaluator_agent",
    port=PORT,
    endpoint=f"{PUBLIC_URL}/submit",
    mailbox=True,
    seed=AGENT_MNEMONIC,
)
proto = Protocol(name="evaluator_protocol")


# ------------------------------------------------------------------------------
# ✅ SSE Notify helper
# ------------------------------------------------------------------------------
async def notify(req_id: str, message: str, done: bool = False, error: bool = False):
    """Send live updates to SSE gateway (Scout-style, low frequency)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                NOTIFY_URL,
                json={"request_id": req_id, "message": message, "done": done, "error": error},
            )
    except Exception as e:
        print(f"[Evaluator Notify Error] {e}")


# ------------------------------------------------------------------------------
# ✅ Optional MeTTa support
# ------------------------------------------------------------------------------
try:
    from hyperon import MeTTa
    HAS_METTA = True
    print("✅ [Evaluator] MeTTa (Hyperon) available")
except Exception as e:
    HAS_METTA = False
    print(f"⚠️  [Evaluator] MeTTa unavailable: {e}")


# ------------------------------------------------------------------------------
# ✅ Weighting configuration
# ------------------------------------------------------------------------------
WEIGHTS = {
    "symbolic": 0.50,
    "compute": 0.35,
    "value":   0.15,
}

COMPUTE_WEIGHTS = {
    "processor": 0.50,
    "warranty":  0.30,
    "shipping":  0.20,
}


# ------------------------------------------------------------------------------
# ✅ Fallback symbolic helpers
# ------------------------------------------------------------------------------
def py_perf_score(specs) -> float:
    cpu_score = 0.85 if ("i7" in specs.processor or "Ryzen 7" in specs.processor) else 0.65
    ram_score = specs.ram_gb / 64.0
    gpu_score = 0.75 if "RTX" in specs.gpu else 0.30
    return (0.4 * cpu_score) + (0.3 * ram_score) + (0.3 * gpu_score)


def py_price_value(price: float, budget: float) -> float:
    if price <= budget:
        return (budget - price) / max(budget, 1e-9)
    return -0.3 * ((price - budget) / max(budget, 1e-9))


def py_review_signal(rating: float, count: int) -> float:
    return (rating / 5.0) * (1.0 if count >= 500 else max(0.0, count / 500.0))


def compute_blend(proc: float, warr: float, ship: float) -> float:
    return (
        COMPUTE_WEIGHTS["processor"] * proc
        + COMPUTE_WEIGHTS["warranty"]  * warr
        + COMPUTE_WEIGHTS["shipping"]  * ship
    )


def fallback_symbolic(l: LaptopOption) -> float:
    perf = py_perf_score(l.specs)
    rev  = py_review_signal(l.rating, l.review_count)
    return 0.7 * perf + 0.3 * rev


# ------------------------------------------------------------------------------
# ✅ Helper utilities
# ------------------------------------------------------------------------------
def build_compute_lookup(scored: Optional[List[ScoredLaptopOption]]) -> Dict[str, Dict[str, float]]:
    if not scored:
        return {}
    return {
        s.base.id: {
            "processor": float(s.processor_score),
            "warranty": float(s.warranty_score),
            "shipping": float(s.shipping_score),
        }
        for s in scored
    }


def parse_metta_scores(metta_result, laptops_by_id: Dict[str, LaptopOption]) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    if not metta_result:
        return scores

    seq = metta_result[0] if isinstance(metta_result, list) and len(metta_result) == 1 else metta_result

    def maybe_float(x):
        try:
            return float(str(x))
        except Exception:
            return None

    items = seq if isinstance(seq, list) else [seq]

    for item in items:
        stack = [item]
        while stack:
            node = stack.pop()
            if hasattr(node, "get_children"):
                children = node.get_children()
                if children and len(children) >= 3 and str(children[0]) == "scored":
                    lid = str(children[1])
                    sc = maybe_float(children[2])
                    if lid in laptops_by_id and sc is not None:
                        scores[lid] = sc
                stack.extend(children)
    return scores


def format_top3_summary(ranked: List[ScoredLaptop]) -> str:
    if not ranked:
        return "No candidates scored."
    medals = ["🥇", "🥈", "🥉"]
    return "Top 3: " + " | ".join(
        f"{medals[i] if i < 3 else i+1}. {r.laptop.model} ({r.score:.2f})"
        for i, r in enumerate(ranked[:3])
    )


# ------------------------------------------------------------------------------
# ✅ Main evaluation handler (unchanged logic)
# ------------------------------------------------------------------------------
@proto.on_message(LaptopEvaluationRequest)
async def handle_eval(ctx: Context, sender: str, msg: LaptopEvaluationRequest):
    if msg.scored_laptops:
        base_laptops: List[LaptopOption] = [s.base for s in msg.scored_laptops]
        compute_map = build_compute_lookup(msg.scored_laptops)
    else:
        base_laptops = msg.laptops or []
        compute_map = {}

    print(f"\n📊 [Evaluator] Received request {msg.request_id}")
    await notify(msg.request_id, "🧠 Evaluator received laptops, preparing for scoring...")

    if not base_laptops:
        await notify(msg.request_id, "⚠️ No laptops provided to Evaluator. Returning empty ranking.", error=True)
        await ctx.send(sender, LaptopEvaluationResult(request_id=msg.request_id, ranked=[]))
        await notify(msg.request_id, "✅ Evaluation result delivered.", done=True)
        return

    ranked: List[ScoredLaptop] = []
    by_id = {l.id: l for l in base_laptops}

    # ---------- MeTTa symbolic scoring ----------
    metta_scores: Dict[str, float] = {}
    metta_used = False

    if HAS_METTA:
        try:
            await notify(msg.request_id, "⚙️ Initializing MeTTa symbolic engine...")
            m = MeTTa()

            kb_path = os.path.join("knowledge", "kb.metta")
            if os.path.exists(kb_path):
                with open(kb_path, "r") as f:
                    m.run(f.read())

            for l in base_laptops:
                atom = (
                    f'(laptop {l.id} '
                    f'"{l.specs.processor}" {l.specs.ram_gb} "{l.specs.gpu}" '
                    f'{l.price} {l.rating} {l.review_count})'
                )
                m.run(f'!(add-atom &self {atom})')

            m.run(f'!(add-atom &self (pref budget {msg.max_budget}))')
            m.run(f'!(add-atom &self (pref prefer_performance {"True" if msg.prefer_performance else "False"}))')

            res = m.run('!(get-laptop-scores)')
            metta_scores = parse_metta_scores(res, by_id)
            metta_used = bool(metta_scores)
            await notify(msg.request_id, f"✅ MeTTa symbolic phase complete (used={metta_used})")

        except Exception as e:
            await notify(msg.request_id, "⚠️ MeTTa unavailable or errored, using fallback symbolic scoring")
    else:
        await notify(msg.request_id, "⚠️ MeTTa disabled or not installed - fallback symbolic scoring active")

    # ---------- Hybrid aggregation ----------
    await notify(msg.request_id, "📦 Blending symbolic + compute + value into hybrid scores...")

    for l in base_laptops:
        symbolic_score = metta_scores.get(l.id, fallback_symbolic(l))
        cs = compute_map.get(l.id, {"processor": 0.5, "warranty": 0.5, "shipping": 0.5})
        compute_component = compute_blend(cs["processor"], cs["warranty"], cs["shipping"])
        value_component = py_price_value(l.price, msg.max_budget)
        final_score = (
            WEIGHTS["symbolic"] * symbolic_score
            + WEIGHTS["compute"] * compute_component
            + WEIGHTS["value"] * value_component
        )

        ranked.append(
            ScoredLaptop(
                laptop=l,
                score=float(final_score),
                symbolic_score=float(symbolic_score),
                compute_score=float(compute_component),
                value_score=float(value_component),
                metta_used=metta_used,
                rationale=(
                    f"hybrid: symbolic={symbolic_score:.3f}, "
                    f"compute={compute_component:.3f}, "
                    f"value={value_component:.3f}"
                    f"{' (metta)' if metta_used else ''}"
                ),
            )
        )

    ranked.sort(key=lambda x: x.score, reverse=True)

    # ---------- Top-3 summary ----------
    await notify(msg.request_id, f"📊 {format_top3_summary(ranked)}")

    # ---------- Send final result ----------
    await notify(msg.request_id, f"✅ Hybrid evaluation complete for {len(ranked)} laptops. Sending results...")
    await ctx.send(sender, LaptopEvaluationResult(request_id=msg.request_id, ranked=ranked))
    await notify(msg.request_id, "✅ Evaluation result delivered.")


# ------------------------------------------------------------------------------
# ✅ Bootstrap
# ------------------------------------------------------------------------------
fund_agent_if_low(evaluator.wallet.address())
evaluator.include(proto, publish_manifest=True)

if __name__ == "__main__":
    print("\n📊 Starting Laptop Evaluator Agent (HYBRID MODE, Scout-style SSE)...")
    print(f"PORT: {PORT}")
    print(f"PUBLIC_URL: {PUBLIC_URL}")
    print(f"NOTIFY_URL: {NOTIFY_URL}")
    print("=" * 80)
    evaluator.run()
