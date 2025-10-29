export interface Requirements {
  quantity: number;
  budget: number;
  use_case?: string;
  min_ram?: number;
  min_storage?: number;
  preferred_brand?: string | null;
  prefer_performance?: boolean;
}

export interface LaptopSpecs {
  processor: string;
  ram_gb: number;
  gpu: string;
}

export interface LaptopCandidate {
  id: string;
  brand: string;
  model: string;
  price: number;
  specs: LaptopSpecs;
  rating: number;
}

export interface RankedLaptop extends LaptopCandidate {
  score: number;
  performance_score: number;
  value_score: number;
  rationale: string;
}

export interface DealSummary {
  model: string;
  brand: string;
  final_unit: number;
  total: number;
  savings: number;
  warranty_years?: number;
  shipping_days?: number;
}

export interface ParsedEvent {
  type: "parsed";
  requestId: string;
  requirements: Requirements;
}

export interface ScoutFoundEvent {
  type: "scout-found";
  requestId: string;
  count: number;
  topCandidates: LaptopCandidate[];
}

export interface MettaDebugEvent {
  type: "metta-debug";
  requestId: string;
  kbLoaded: boolean;
  atomsPreview: string[];
  calcTest: string;
}

export interface RankedEvent {
  type: "ranked";
  requestId: string;
  ranked: RankedLaptop[];
}

export interface NegotiationEvent {
  type: "negotiation";
  requestId: string;
  original: number;
  discount_pct: number;
  final_unit: number;
  quantity: number;
  target: number;
}

export interface DoneEvent {
  type: "done";
  requestId: string;
  accepted: boolean;
  summary: DealSummary;
}

export type ProcureEvent =
  | ParsedEvent
  | ScoutFoundEvent
  | MettaDebugEvent
  | RankedEvent
  | NegotiationEvent
  | DoneEvent;
