# Procura — Autonomous Multi-Agent Procurement System

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

Procura transforms a single sentence—*"I need 5 laptops for video editing under $1500 each"*—into a **fully reasoned, cost-optimized procurement decision** using collaborating AI agents, symbolic reasoning, compute scoring, and simulated negotiation.

Built with **Fetch.ai's uAgents framework** and **SingularityNET's MeTTa Knowledge Graph**, Procura demonstrates autonomous multi-agent collaboration across the ASI Alliance ecosystem.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Agent Registry](#agent-registry)
- [Interfaces](#interfaces)
- [Technology Stack](#technology-stack)
- [Data & Reasoning Layers](#data--reasoning-layers)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Output Example](#output-example)
- [Project Structure](#project-structure)
- [License](#license)

---

## Overview

Procura is an **autonomous multi-agent procurement system** that eliminates the time-consuming process of sourcing, comparing, and negotiating hardware purchases. Instead of spending hours researching suppliers and specifications, users simply describe their needs in natural language, and Procura's specialized agents handle the rest.

**The Problem**: Traditional procurement requires manual research across multiple suppliers, comparison of technical specifications, price negotiation, and risk assessment—often taking days or weeks.

**The Solution**: Procura orchestrates five specialized agents that collaborate to deliver a justified procurement recommendation in seconds, complete with negotiated pricing and technical rationale.

**Live Demos**: Search for the orchestration agent on Agentverse to run the workflow (agent1qvwa3w9v2qpe8g87mwcnnsrdq30q7yst077gns8pm9l9ukxrkm8ysvtzgqc). Visit https://pronet-xi.vercel.app/ to see a live UI connecting with the ASI network. 

---

## Key Features

✅ **Natural Language Interface** — Interact via ASI:One Chat Protocol or optional web UI  
✅ **Multi-Agent Orchestration** — Five specialized agents with single-responsibility design  
✅ **Ocean Protocol Mocked Integration** — Supplier data discovery with provenance metadata  
✅ **CUDOS Compute Mocked Scoring** — Hardware performance evaluation using weighted compute metrics  
✅ **MeTTa Symbolic Reasoning** — Logic-based suitability analysis and preference modeling  
✅ **Automated Negotiation** — Bulk pricing optimization with elasticity modeling  
✅ **Full Transparency** — Every decision step is logged and explainable 

**Live Demos**: Search for the orchestration agent on Agentverse to run the workflow on Agentverse. (agent1qvwa3w9v2qpe8g87mwcnnsrdq30q7yst077gns8pm9l9ukxrkm8ysvtzgqc). Visit https://pronet-xi.vercel.app/.

---

## Architecture

### High-Level Flow

```
Primary Interface (No UI Required):
┌─────────────┐
│  ASI:One    │ ← User: "I need 5 laptops for video editing under $1500 each"
│  Chat       │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENT ORCHESTRATION LAYER                         │
├─────────────────────────────────────────────────────────────────────┤
│  orchestrator → scout → compute → evaluator → negotiator → Result   │
└─────────────────────────────────────────────────────────────────────┘

Optional Interface (Visualization):
┌──────────────┐      HTTP        ┌──────────────┐
│   React UI   │ ←─────────────→  │   Gateway    │
│              │      SSE         │   Agent      │
└──────────────┘                  └──────┬───────┘
                                         │
                                         ↓
                                  (connects to orchestrator)
```

### Design Principles

- **Single Responsibility** — Each agent has one clear purpose
- **Message Passing Only** — No shared global state; all data flows through messages
- **Deterministic Pipeline** — Same input always produces same output
- **Inspectable State** — Every intermediate result is logged and traceable
- **Decoupled Components** — Agents can be updated independently

---

## Agent Registry

All agents are registered on **Agentverse** with the **Chat Protocol enabled** for ASI:One integration.

| Agent Name             | Responsibility                                                  | Identity Key                                                       |
|------------------------|----------------------------------------------------------------|--------------------------------------------------------------------|
| **orchestrator_agent** | Workflow coordination, intent parsing, task routing             | `db3291e977ba0c29e88b7ce0563c00a0a383f00a0f908f91f7de4db61cd98a91` |
| **scout_agent**        | Product/supplier discovery with Ocean Protocol-style metadata  | `14f0a49a99d72d2e1a20464fe2d32e74a52837295979f7050ecc52968ce46c7a` |
| **compute_agent**      | CUDOS-style weighted performance/value scoring                  | `7afc8286e3e8bb10b6bb6a30862562c4a12da759421ff1fc92e06b51e99c459f` |
| **evaluator_agent**    | MeTTa symbolic reasoning for suitability ranking                | `754f8cfca0608dd2a9347fe1179b523a2f38b16938098d3245369331a3b71b46` |
| **negotiator_agent**   | Bulk pricing strategy, discount optimization, deal finalization | `99cf6671fe37e33776c6fcbb4561a1e8fcc11bfb3ad4e85c3d7180094fbba85f` |
| **gateway_agent**      | (Optional) HTTP UI ↔ Agentverse bridge with SSE streaming       | `c4c25ebca140677fd1849dd07c9342509696ba1299c306cef39d5edb702a1b8f` |

> **Note**: Agent addresses are printed on launch. The identity keys above are for reference.

---

## Interfaces

### 1) Primary: ASI:One Chat Protocol (Recommended)

The primary interface uses Fetch.ai's **Chat Protocol** to enable direct natural language interaction through **ASI:One**.

**Example Interaction:**

```
User: I need 5 laptops for video editing under $1500 each.

Orchestrator: Request parsed. Delegating to Scout for supplier filtering...

Scout: Found 12 candidates matching constraints. Adding Ocean metadata...

Compute: Scoring hardware performance using CUDOS weights...

Evaluator: Running MeTTa reasoning for suitability analysis...

Negotiator: Applying bulk discount strategy for quantity 5...

Result: 
┌─────────────────────────────────────────────────┐
│ Recommendation: ASUS ProArt P16                 │
│ Negotiated Unit Price: $1,139.00                │
│ Quantity: 5                                     │
│ Total Cost: $5,695.00                           │
│ Savings: $300 (5% bulk + performance bonus)     │
│                                                 │
│ Why: Best sustained GPU + RAM under budget;     │
│ excellent review depth; fast shipping;          │
│ supplier supports tiered bulk discount.         │
│                                                 │
│ Top-3 Alternatives:                             │
│ 1. ASUS ProArt P16 - $1,139                     │
│ 2. Lenovo Legion Pro 5 - $1,289                 │
│ 3. MSI Creator M16 - $1,399                     │
└─────────────────────────────────────────────────┘
```

### 2) Secondary: Web UI + Gateway Agent (Optional)

For visualization and debugging, an optional React frontend connects through the **gateway_agent**.

```
Frontend (React + Tailwind)
    ↓ POST /api/procure
Gateway Agent
    ↓ uAgent messages
Orchestrator → Scout → Compute → Evaluator → Negotiator
    ↓ SSE updates
Frontend (live progress stream)
```

The gateway agent contains **no decision logic**—it only translates between HTTP/SSE and agent messages.

---

## Technology Stack

### ASI Alliance Technologies

| Technology               | Purpose                                                      |
|--------------------------|--------------------------------------------------------------|
| **Fetch.ai uAgents**     | Core agent framework, message passing, Agentverse registry   |
| **SingularityNET MeTTa** | Symbolic reasoning engine for suitability evaluation         |
| **Ocean Protocol**       | Supplier data discovery pattern with metadata (mocked)       |
| **CUDOS**                | Compute-to-score pattern for performance evaluation (mocked) |

### Supporting Technologies

- **Python 3.10+** — Agent runtime
- **FastAPI** — Backend API for optional UI
- **React + Tailwind** — Optional frontend
- **Server-Sent Events (SSE)** — Real-time progress streaming

---

## Data & Reasoning Layers

### 1. Ocean-Style Supplier Discovery (Scout Agent)

The scout agent discovers suppliers and annotates each procurement run with **Ocean Protocol-inspired metadata** for data provenance and quality tracking.

**Metadata Structure:**

```python
def generate_ocean_metadata():
    return {
        "data_source": "ocean-protocol",
        "datatoken_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "dataset_name": "Enterprise Laptop Suppliers Q4 2025",
        "access_type": "compute-to-data",
        "data_quality_score": round(random.uniform(0.85, 0.98), 2),
        "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
        "provider": "TechSupply DataMarket",
        "license": "CC-BY-4.0",
        "verification_method": "third-party-audit"
    }
```

**Laptop Record Example:**

```json
{
  "id": "lap-001",
  "model": "ASUS ProArt P16",
  "brand": "ASUS",
  "specs": {
    "processor": "AMD Ryzen 9 7945HX",
    "ram_gb": 32,
    "storage_gb": 1000,
    "gpu": "NVIDIA RTX 4060",
    "screen_size": 16,
    "weight_lbs": 4.8
  },
  "price": 1199.00,
  "supplier": "TechDirect Wholesale",
  "rating": 4.7,
  "review_count": 542,
  "shipping_days": 5,
  "warranty_years": 2,
  "stock": 87,
  "use_cases": ["video-editing", "3d-modeling", "gaming"],
  "bulk_pricing": [
    { "min_qty": 5, "discount_pct": 5 },
    { "min_qty": 10, "discount_pct": 8 },
    { "min_qty": 25, "discount_pct": 12 }
  ]
}
```

The scout filters candidates by:
- Budget constraints
- Use case requirements
- Stock availability
- Delivery timeline
- Warranty requirements

---

### 2. CUDOS-Style Compute Scoring (Compute Agent)

Hardware performance is evaluated using a **weighted compute scoring system** inspired by CUDOS's compute-to-score architecture.

**Scoring Weights Configuration:**

```json
{
  "processor_weights": {
    "AMD Ryzen 9": 0.95,
    "Intel Core i9": 0.92,
    "Apple M2 Pro": 0.90,
    "Intel Core i7": 0.85,
    "AMD Ryzen 7": 0.82,
    "Intel Core i5": 0.75,
    "Apple M2": 0.78
  },
  "gpu_weights": {
    "NVIDIA RTX 4090": 1.00,
    "NVIDIA RTX 4080": 0.92,
    "NVIDIA RTX 4070": 0.85,
    "NVIDIA RTX 4060": 0.78,
    "AMD Radeon RX 7900": 0.88
  },
  "max_warranty_years": 3,
  "max_shipping_days": 10,
  "max_ram_gb": 64
}
```

**Scoring Dimensions:**

1. **CPU Performance** — Normalized by processor family weight
2. **GPU Capability** — Weighted for compute-intensive tasks
3. **RAM Capacity** — Normalized against maximum (64GB)
4. **Value Score** — Price efficiency relative to budget
5. **Warranty Coverage** — Normalized against maximum (3 years)
6. **Shipping Speed** — Inverse normalization (faster = better)

**Composite Score Formula:**

```
compute_score = (
    0.30 × cpu_normalized +
    0.25 × gpu_normalized +
    0.20 × ram_normalized +
    0.15 × value_normalized +
    0.05 × warranty_normalized +
    0.05 × shipping_normalized
)
```

**Output Example:**

```json
{
  "laptop_id": "lap-001",
  "compute_score": 0.87,
  "breakdown": {
    "cpu_score": 0.95,
    "gpu_score": 0.78,
    "ram_score": 0.50,
    "value_score": 0.92,
    "warranty_score": 0.67,
    "shipping_score": 0.50
  }
}
```

This approach mirrors how CUDOS evaluates compute resources, providing transparent, reproducible performance metrics.

---

### 3. MeTTa Symbolic Reasoning (Evaluator Agent)

The evaluator agent uses **SingularityNET's MeTTa** to perform symbolic reasoning over candidates, blending quantitative metrics with qualitative preferences.

#### Why MeTTa?

MeTTa (Meta Type Talk) is a language designed for symbolic AI reasoning, enabling:
- **Declarative logic rules** instead of imperative code
- **Pattern matching** over knowledge graphs
- **Compositional reasoning** that explains decisions
- **Human-readable rule definitions**

#### MeTTa Reasoning Components

**1. Knowledge Base Population:**

The evaluator injects laptop data and user preferences into a MeTTa knowledge space:

```metta
; Laptop knowledge atoms
(laptop lap-001 "AMD Ryzen 9" 32 "RTX 4060" 1199.00 4.7 542)
(laptop lap-002 "Intel Core i7" 16 "RTX 4050" 1089.00 4.5 318)
(laptop lap-003 "AMD Ryzen 7" 32 "RTX 4070" 1449.00 4.8 627)

; User preferences
(pref budget 1500.00)
(pref prefer_performance True)
(pref min_ram 16)
```

**2. Scoring Functions:**

```metta
; -------------------------
; Component scoring functions
; -------------------------

; RAM score: Normalize RAM against a 32GB baseline
(= (ram-score $ram) (/ $ram 32))

; Price score: Reward staying under budget, penalize overages
(= (price-score $price $budget)
   (if (<= $price $budget)
       (/ (- $budget $price) $budget)      ; More headroom = better
       (* -0.3 (/ (- $price $budget) $budget))))  ; Penalize overages

; Rating score: Weight rating by review depth
(= (rating-score $rating $count)
   (* (/ $rating 5.0)
      (if (>= $count 500) 
          1.0 
          (/ $count 500))))  ; Discount ratings with few reviews

; GPU score: Use processor as proxy for overall compute capability
(= (gpu-score $gpu)
   (match $gpu
     ("RTX 4090" 1.00)
     ("RTX 4080" 0.92)
     ("RTX 4070" 0.85)
     ("RTX 4060" 0.78)
     ("RTX 4050" 0.70)
     ($_ 0.60)))  ; Default for unknown GPUs
```

**3. Preference-Aware Weighting:**

The system adjusts scoring weights based on user preferences:

```metta
; Performance-focused weighting (prefer_performance = True)
; Emphasizes RAM and GPU capability over price
(= (weighted-score $ram-norm $price-norm $rating-norm $gpu-norm True)
   (+ (+ (* 0.35 $ram-norm) 
         (* 0.20 $price-norm))
      (+ (* 0.20 $rating-norm)
         (* 0.25 $gpu-norm))))

; Budget-focused weighting (prefer_performance = False)
; Emphasizes price efficiency over specs
(= (weighted-score $ram-norm $price-norm $rating-norm $gpu-norm False)
   (+ (+ (* 0.20 $ram-norm) 
         (* 0.45 $price-norm))
      (+ (* 0.20 $rating-norm)
         (* 0.15 $gpu-norm))))
```

**4. Main Scoring Logic:**

```metta
; -------------------------
; Main scoring function
; -------------------------
(= (calc-laptop-score $ram $price $budget $rating $count $gpu $prefer)
   (weighted-score (ram-score $ram)
                   (price-score $price $budget)
                   (rating-score $rating $count)
                   (gpu-score $gpu)
                   $prefer))

; -------------------------
; Query all laptop scores
; -------------------------
(= (get-laptop-scores)
   (collapse 
     (match &self (laptop $id $cpu $ram $gpu $price $rating $count)
       (match &self (pref budget $budget)
         (match &self (pref prefer_performance $prefer)
           (scored $id 
                   (calc-laptop-score $ram $price $budget $rating $count $gpu $prefer)
                   metta))))))
```

**5. Ranking & Explanation Generation:**

```metta
; -------------------------
; Get top N ranked candidates
; -------------------------
(= (get-top-ranked $n)
   (let $scores (get-laptop-scores)
     (take $n (sort-desc $scores))))

; -------------------------
; Generate human-readable explanation
; -------------------------
(= (explain-score $id)
   (match &self (laptop $id $cpu $ram $gpu $price $rating $count)
     (match &self (scored $id $score metta)
       (explanation $id 
         (concat "Score: " (str $score) 
                 " | RAM: " (str $ram) "GB"
                 " | Price: $" (str $price)
                 " | Rating: " (str $rating) 
                 " (" (str $count) " reviews)")))))
```

#### MeTTa Output Example

```python
# Python interface with MeTTa runner
runner = MeTTaRunner()
runner.load_knowledge(laptop_atoms, preference_atoms)

result = runner.run("!(get-top-ranked 3)")

# Output:
# [
#   (scored lap-001 0.847 metta),
#   (scored lap-003 0.812 metta),
#   (scored lap-002 0.768 metta)
# ]

explanations = runner.run("!(explain-score lap-001)")

# Output:
# (explanation lap-001 
#   "Score: 0.847 | RAM: 32GB | Price: $1199.00 | Rating: 4.7 (542 reviews)")
```

#### Hybrid Scoring

The evaluator combines three scoring dimensions into a final hybrid score:

```python
final_score = (0.50 × symbolic_score) + (0.35 × compute_score) + (0.15 × value_score)
```

**Scoring Components:**
- **Symbolic Score (50%)** — MeTTa reasoning or fallback heuristics for suitability
- **Compute Score (35%)** — CUDOS-style hardware performance evaluation
- **Value Score (15%)** — Price efficiency relative to budget constraints

This tri-factor approach provides:
- **Quantitative rigor** from compute scoring
- **Qualitative reasoning** from MeTTa logic
- **Cost optimization** from value analysis
- **Explainability** through transparent weight allocation
- **Flexibility** to adjust preference weights per use case

**Result**: Top-3 ranked candidates with justified reasoning for each placement.

---

### 4. Negotiation Logic (Negotiator Agent)

The negotiator agent simulates a procurement officer's strategy, combining:
- **Tiered bulk discounts** from supplier pricing tables
- **Performance-based elasticity** (better products warrant smaller discounts)
- **Stock feasibility** checks
- **Delivery timeline optimization**

**Negotiation Formula:**

```python
base_price = candidate["price"]
tier_discount = get_bulk_discount(quantity, candidate["bulk_pricing"])
performance_bonus = calculate_elasticity(compute_score, metta_score)

negotiated_unit = base_price × (1 - tier_discount - performance_bonus)
total_cost = negotiated_unit × quantity
savings_pct = ((base_price × quantity) - total_cost) / (base_price × quantity) × 100
```

**Example Calculation:**

```
Candidate: ASUS ProArt P16
Base price: $1,199.00
Quantity: 5
Tier discount (5+ units): 5%
Performance bonus (high scores): 1.5%

Negotiated unit price = $1,199 × (1 - 0.05 - 0.015) = $1,139.01
Total cost = $1,139.01 × 5 = $5,695.05
Savings = $299.95 (5.0%)
```

**Output:**

```json
{
  "recommended_model": "ASUS ProArt P16",
  "negotiated_unit_price": 1139.01,
  "quantity": 5,
  "total_cost": 5695.05,
  "savings_pct": 5.0,
  "deal_notes": "Tier discount applied at qty 5. High performance score warranted minimal additional negotiation. Stock confirmed, 5-day delivery available.",
  "top_3": [
    {"model": "ASUS ProArt P16", "price": 1139.01, "score": 0.87},
    {"model": "Lenovo Legion Pro 5", "price": 1289.00, "score": 0.81},
    {"model": "MSI Creator M16", "price": 1399.00, "score": 0.77}
  ]
}
```

---

## Installation & Setup

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** (for optional UI)
- **uAgents Framework**: `pip install uagents`
- **MeTTa**: `pip install hyperon` (SingularityNET's Python binding)

### 1. Clone Repository

```bash
git clone https://github.com/stuckertks09/procurapublic.git
cd procura
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Requirements.txt:**
```
uagents==0.8.0
hyperon==0.3.0
fastapi==0.104.0
uvicorn==0.24.0
pydantic==2.5.0
httpx==0.25.0
```

### 3. Start Backend API

```bash
uvicorn backend.main:app --reload --port 9000
```

This provides:
- `POST /api/procure` — Submit procurement request
- `GET /api/stream/{request_id}` — SSE progress stream
- `POST /api/notify` — Agent update webhook
- `GET /api/laptops` — Dataset endpoint
- `POST /api/score` — Compute scoring endpoint

### 4. Start Agents

1. Run Python run_local.py

OR:

2. Open **separate terminal windows** for each agent:

```bash
# Terminal 1 — Orchestrator
python -m agents.orchestrator

# Terminal 2 — Scout
python -m agents.scout

# Terminal 3 — Compute (leave as compute_agent)
python -m agents.compute_agent

# Terminal 4 — Evaluator
python -m agents.evaluator

# Terminal 5 — Negotiator
python -m agents.negotiator

# Terminal 6 (optional, for UI / HTTP gateway)
python -m agents.gateway_agent

Each agent will print its **Agentverse address** on startup.

### 5. Start Frontend (Optional)

```bash
cd frontend
npm install
npm run dev
```

Access UI at `http://localhost:PORT`

---

## Usage

## Via Local Test

1. Run Python Test.py

### Via ASI:One Chat Protocol (Primary)

1. Ensure all agents are running and registered on **Agentverse**
2. Enable **Chat Protocol** for the **orchestrator_agent**
3. Open **ASI:One** interface
4. Send a natural language request:

```
I need 5 laptops for video editing under $1500 each.
```

5. Observe the multi-agent pipeline in action:
   - Orchestrator parses intent
   - Scout discovers candidates
   - Compute scores hardware
   - Evaluator reasons symbolically
   - Negotiator finalizes deal

6. Receive structured recommendation with:
   - Top-3 ranked options
   - Negotiated pricing
   - Detailed rationale
   - Procurement action plan

### Via HTTP API (Optional)

**Submit Request:**

```bash
curl -X POST http://localhost:9000/api/procure \
  -H "Content-Type: application/json" \
  -d '{
    "use_case": "video-editing",
    "quantity": 5,
    "budget": 1500,
  }'

# Response:
# {"request_id": "req-abc123", "status": "processing"}
```

**Stream Progress:**

```bash
curl -N http://localhost:9000/api/stream/req-abc123

# SSE Stream:
# event: scout_started
# data: {"message": "Filtering suppliers by constraints..."}
#
# event: scout_complete
# data: {"candidates": 12, "ocean_metadata": {...}}
#
# event: compute_started
# data: {"message": "Scoring hardware performance..."}
# ...
```

### Via Web UI Demo (Optional)

1. Navigate to `https://localhost:PORT`
2. Fill out procurement form:
   - Use case (dropdown)
   - Quantity (number)
   - Budget per unit ($)
   - Performance preference (toggle)
   - GPU required (checkbox)
3. Click "Submit"
4. Watch live progress timeline
5. Review Top-3 shortlist table
6. View final deal summary card
7. Print a Purchase Order PDF

---

## Output Example

### Console Output

```
╔══════════════════════════════════════════════════════════════════╗
║                    PROCUREMENT RECOMMENDATION                     ║
╠══════════════════════════════════════════════════════════════════╣
║ Model:            ASUS ProArt P16                                ║
║ Unit Price:       $1,199.00 → $1,139.00 (negotiated)            ║
║ Quantity:         5 units                                        ║
║ Total Cost:       $5,695.00                                      ║
║ Savings:          $300.00 (5.0%)                                 ║
╠══════════════════════════════════════════════════════════════════╣
║ RATIONALE                                                        ║
║ • Best sustained GPU + RAM combination under budget              ║
║ • Excellent review depth (542 reviews, 4.7★)                    ║
║ • Fast shipping (5 days)                                         ║
║ • Supplier supports tiered bulk discount at qty 5               ║
║ • MeTTa reasoning: High performance alignment with use case     ║
║ • CUDOS score: 0.87 (top 8th percentile)                        ║
╠══════════════════════════════════════════════════════════════════╣
║ TOP-3 ALTERNATIVES                                               ║
║ 1. ASUS ProArt P16      $1,139  Score: 0.87  [RECOMMENDED]      ║
║ 2. Lenovo Legion Pro 5  $1,289  Score: 0.81                     ║
║ 3. MSI Creator M16      $1,399  Score: 0.77                     ║
╚══════════════════════════════════════════════════════════════════╝
```

### JSON Response

```json
{
  "request_id": "req-abc123",
  "recommendation": {
    "model": "ASUS ProArt P16",
    "brand": "ASUS",
    "base_price": 1199.00,
    "negotiated_unit_price": 1139.01,
    "quantity": 5,
    "total_cost": 5695.05,
    "savings": 299.95,
    "savings_pct": 5.0
  },
  "rationale": {
    "primary_strengths": [
      "Best GPU + RAM under budget",
      "High review confidence (542 reviews)",
      "Fast delivery (5 days)"
    ],
    "compute_score": 0.87,
    "metta_score": 0.85,
    "final_score": 0.86,
    "ocean_metadata": {
      "data_source": "ocean-protocol",
      "dataset_name": "Enterprise Laptop Suppliers Q4 2025",
      "data_quality_score": 0.94
    }
  },
  "top_3": [
    {
      "rank": 1,
      "model": "ASUS ProArt P16",
      "price": 1139.01,
      "score": 0.87
    },
    {
      "rank": 2,
      "model": "Lenovo Legion Pro 5",
      "price": 1289.00,
      "score": 0.81
    },
    {
      "rank": 3,
      "model": "MSI Creator M16",
      "price": 1399.00,
      "score": 0.77
    }
  ],
  "pipeline_log": [
    {"agent": "orchestrator", "timestamp": "2025-10-28T10:15:23Z", "action": "parsed_intent"},
    {"agent": "scout", "timestamp": "2025-10-28T10:15:24Z", "action": "filtered_12_candidates"},
    {"agent": "compute", "timestamp": "2025-10-28T10:15:26Z", "action": "scored_hardware"},
    {"agent": "evaluator", "timestamp": "2025-10-28T10:15:28Z", "action": "metta_reasoning_complete"},
    {"agent": "negotiator", "timestamp": "2025-10-28T10:15:30Z", "action": "finalized_deal"}
  ]
}
```

---

## Project Structure

```
procura/
├── agents/
│   ├── orchestrator_agent.py    # Workflow coordinator (Chat Protocol enabled)
│   ├── scout_agent.py           # Supplier discovery with Ocean metadata
│   ├── compute_agent.py         # CUDOS-style hardware scoring
│   ├── evaluator_agent.py       # MeTTa symbolic reasoning
│   ├── negotiator_agent.py      # Bulk pricing negotiation
│   └── gateway_agent.py         # HTTP ↔ uAgent bridge (optional)
│
├── backend/
│   ├── __init__.py
│   └── main.py                  # FastAPI server
│
├── data/
│   ├── laptops.json             # Supplier dataset
│   └── scoring_factors.json     # Compute weights configuration
│
├── frontend/                    # Optional React + TypeScript UI
│   ├── src/
│   │   ├── pages/
│   │   │   └── ProcurePage.tsx  # Main procurement interface
│   │   ├── components/          # UI components
│   │   ├── hooks/               # React hooks
│   │   ├── types/               # TypeScript definitions
│   │   ├── assets/              # Static assets
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── main.tsx
│   │   └── index.css
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── README.md
│
├── knowledge/
│   └── kb.metta                 # MeTTa knowledge base & rules
│
├── venv/                        # Python virtual environment
│
├── .env.compute.example         # Environment config templates
├── .env.evaluator.example
├── .env.main.example
├── .env.negotiator.example
├── .env.orchestrator.example
├── .env.scout.example
├── private_keys.json            # Agent identity keys
├── requirements.txt             # Python dependencies
├── run_local.py                 # Local development launcher
├── test.py                      # Test suite
└── README.md                    # This file
```

---

## API Reference

### Backend Endpoints

| Method | Endpoint                   | Purpose                                           |
|--------|----------------------------|---------------------------------------------------|
| `POST` | `/api/procure`             | Submit procurement request; returns `request_id`  |
| `GET`  | `/api/stream/{request_id}` | Server-Sent Events stream of agent progress       |
| `POST` | `/api/notify`              | Webhook for agents to post progress updates       |
| `GET`  | `/api/laptops`             | Retrieve laptop dataset (for scout_agent)         |
| `POST` | `/api/score`               | Compute scoring endpoint (for compute_agent)      |

### Agent Messages

**Orchestrator → Scout:**
```python
{
  "type": "find_candidates",
  "use_case": "video-editing",
  "budget": 1500,
  "quantity": 5,
  "constraints": {"min_ram_gb": 16, "required_gpu": true}
}
```

**Scout → Compute:**
```python
{
  "type": "score_candidates",
  "candidates": [...],  # List of laptop objects
  "ocean_metadata": {...}
}
```

**Compute → Evaluator:**
```python
{
  "type": "evaluate_suitability",
  "scored_candidates": [...],  # With compute_score added
  "user_preferences": {"prefer_performance": true}
}
```

**Evaluator → Negotiator:**
```python
{
  "type": "negotiate_deal",
  "top_3": [...],  # With metta_score and final_score
  "quantity": 5,
  "budget": 1500
}
```

**Negotiator → Orchestrator:**
```python
{
  "type": "procurement_complete",
  "recommendation": {...},
  "rationale": {...},
  "top_3": [...]
}
```

---

## License

**Open Source - Free to Use**

This agent and all associated code are released under the **MIT License**.

**You are free to**:
- ✅ Use commercially
- ✅ Modify and adapt
- ✅ Distribute
- ✅ Use privately
- ✅ Sublicense

**No warranty provided. Use at your own risk.**

Full license text available in repository.

---

## Acknowledgments

Built for the **ASI Alliance Hackathon** using:
- **Fetch.ai** uAgents Framework
- **SingularityNET** MeTTa Knowledge Graph
- **Ocean Protocol** data discovery patterns
- **CUDOS** compute scoring architecture

**Author**: Kurtis Stuckert  
**Repository**: https://github.com/stuckertks09/procurapublic
**Demo Video**: https://storage.googleapis.com/my-ads-creatives/ads/test/procura.mp4

---

## Support

For questions or issues:
- Open a GitHub issue
- Contact via ASI Alliance Discord
- Email: [Stuckertks09@gmail.com]

---

**Procura proves multi-agent autonomy: data-driven, symbolic, and commercially realistic—in one pipeline.**