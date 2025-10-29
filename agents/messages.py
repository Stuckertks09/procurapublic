from pydantic.v1 import BaseModel, Field
from typing import List, Optional
from uuid import uuid4
from uagents import Model

def make_req_id() -> str:
    return str(uuid4())

# -----------------------------
# LAPTOP-SPECIFIC DATA MODELS
# -----------------------------
class LaptopSpecs(BaseModel):
    """Nested specs model"""
    processor: str
    ram_gb: int
    storage_gb: int
    gpu: str
    screen_size: float
    weight_lbs: float

class BulkPricing(BaseModel):
    """Bulk discount tier"""
    min_qty: int
    discount_pct: float

class OceanMeta(BaseModel):
    data_source: str = "ocean-protocol"
    datatoken_address: str
    dataset_name: str
    access_type: str = "compute-to-data"
    data_quality_score: float
    last_updated: str

class CudosMeta(BaseModel):
    compute_job_id: str
    network: str = "cudos-mainnet"
    compute_cost: str
    execution_time_ms: int
    node_location: str

class LaptopOption(BaseModel):
    """Represents a laptop from the catalog"""
    id: str
    model: str
    brand: str
    specs: LaptopSpecs
    price: float
    supplier: str
    rating: float
    review_count: int
    shipping_days: int
    warranty_years: int
    stock: int
    use_cases: List[str]
    bulk_pricing: List[BulkPricing]

class ScoredLaptopOption(BaseModel):
    base: LaptopOption
    processor_score: float
    warranty_score: float
    shipping_score: float
    cudos_meta: dict

class LaptopScoredResponse(Model):   # ✅ CHANGE BaseModel -> Model
    request_id: str
    laptops: List[ScoredLaptopOption]

# -----------------------------
# ORCHESTRATOR → SCOUT
# -----------------------------
class ProcurementRequest(Model):
    """User's laptop requirements"""
    request_id: str = Field(default_factory=make_req_id)
    use_case: str  # "video-editing", "programming", "office-work"
    quantity: int
    max_budget_per_unit: float
    min_ram_gb: Optional[int] = None
    min_storage_gb: Optional[int] = None
    preferred_brand: Optional[str] = None
    prefer_performance: bool = True  # vs prefer_cost

# -----------------------------
# SCOUT → ORCHESTRATOR
# -----------------------------
class LaptopResponse(Model):
    request_id: str
    laptops: List[LaptopOption]

# -----------------------------
# ORCHESTRATOR → EVALUATOR
# -----------------------------
class LaptopEvaluationRequest(Model):
    request_id: str
    laptops: Optional[List[LaptopOption]] = None  # keep old support
    scored_laptops: Optional[List[ScoredLaptopOption]] = None
    use_case: str
    quantity: int
    max_budget: float
    prefer_performance: bool = True

# -----------------------------
# EVALUATOR → ORCHESTRATOR
# -----------------------------
class ScoredLaptop(BaseModel):
    laptop: LaptopOption
    score: float                     # Final hybrid weighted score
    symbolic_score: float            # From MeTTa or fallback symbolic logic
    compute_score: float             # Weighted compute blend
    value_score: float               # Price vs budget pressure
    metta_used: bool                 # True if MeTTa was used
    rationale: str                   # Human-readable breakdown

class LaptopEvaluationResult(Model):
    request_id: str
    ranked: List[ScoredLaptop]

# -----------------------------
# ORCHESTRATOR → NEGOTIATOR
# -----------------------------
class BulkNegotiationRequest(Model):
    request_id: str
    top_pick: ScoredLaptop
    quantity: int
    target_price_per_unit: Optional[float] = None

# -----------------------------
# NEGOTIATOR → ORCHESTRATOR
# -----------------------------
class BulkNegotiationResult(Model):
    request_id: str
    accepted: bool
    original_price: float
    final_price_per_unit: float
    total_cost: float
    discount_applied_pct: float
    savings: float
    note: Optional[str] = None