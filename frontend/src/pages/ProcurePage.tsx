import { useMemo, useRef, useState } from "react";
import jsPDF from "jspdf";

export default function ProcurePage() {
  const [useCase, setUseCase] = useState("video-editing");
  const [quantity, setQuantity] = useState(5);
  const [budget, setBudget] = useState(1500);

  const [messages, setMessages] = useState<string[]>([]);
  const [scoutCount, setScoutCount] = useState<number | null>(null);
  const [finalPrice, setFinalPrice] = useState<number | null>(null);
  const [completed, setCompleted] = useState(false);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);


  const eventSourceRef = useRef<EventSource | null>(null);

  const USE_CASE_OPTIONS = [
  "ai-ml",
  "architecture",
  "business-travel",
  "chrome-os",
  "consulting",
  "data-science",
  "design",
  "education",
  "executive-use",
  "game-development",
  "gaming",
  "light-productivity",
  "music-production",
  "office-work",
  "presentations",
  "remote-work",
  "software-development",
  "video-editing",
  "3d-modeling"
].sort();

 // -------------------------------
// Stream Parser
// -------------------------------
type ParsedEvent =
  | { type: "model"; name: string }
  | { type: "scout"; count: number }
  | { type: "negotiation"; finalUnit: number }
  | { type: "done" }
  | { type: "log"; text: string };

function parseEvent(raw: string): ParsedEvent {
  // Strip leading timestamps and formatting if present
  const msg = raw.replace(/^\[.*?\]\s*/, "").trim();

  // --- Model Selection (e.g. "Sending top choice to Negotiator: ASUS ProArt P16")
  const modelMatch = msg.match(/sending top choice to negotiator:\s*(.*)/i);
  if (modelMatch) {
    const name = modelMatch[1].trim();
    if (name.length > 0) return { type: "model", name };
  }

  // --- Scout Phase (e.g. "Scout Agent found 5 candidates")
  const scoutMatch = msg.match(/scout(?:\sagent)?\s.*?found\s+(\d+)/i);
  if (scoutMatch) return { type: "scout", count: Number(scoutMatch[1]) };

  // --- Final Unit Price Negotiation
  const priceMatch =
    msg.match(/final (?:negotiated )?price(?: per unit)?:?\s*\$?([\d.,]+)/i) ||
    msg.match(/negotiated price.*?\$?([\d.,]+)/i);

  if (priceMatch) {
    const num = Number(String(priceMatch[1]).replace(/,/g, ""));
    if (!Number.isNaN(num)) return { type: "negotiation", finalUnit: num };
  }

  // --- Completion (finalization signal from any agent)
  if (/(deal complete|accepted|evaluation result delivered|done)/i.test(msg)) {
    return { type: "done" };
  }

  // --- Default log line
  return { type: "log", text: msg };
}


  function generatePDF() {
  if (finalPrice === null) return; // nothing to generate until pricing is done

  const doc = new jsPDF({ unit: "pt" });
  const date = new Date().toLocaleDateString();
  const total = finalPrice * quantity;

  doc.setFont("helvetica", "normal");

  // Header
  doc.setFontSize(18);
  doc.text("PURCHASE ORDER (PO)", 40, 50);
  doc.setFontSize(13);
  doc.text("Multi-Agent Procurement System", 40, 70);

  // Vendor + Meta Info
  doc.setFontSize(9);
  doc.text(`Vendor: Tech Company R US`, 40, 110);
  doc.text(`PO Date: ${date}`, 400, 110);

  doc.text(`Ship To: Cendral AI`, 40, 130);
  if (requestId) doc.text(`Reference: ${requestId}`, 40, 150);

  // Spacer Line
  doc.line(40, 160, 550, 160);

  // Table Header
  let y = 190;
  doc.setFontSize(9);
  doc.text("Model", 40, y);
  doc.text("Qty", 260, y);
  doc.text("Unit Price", 330, y);
  doc.text("Total", 450, y);

  y += 8;
  doc.line(40, y, 550, y); // underline header
  y += 20;

  // Placeholder model name because we do not have final model selection in streaming data
  const model = selectedModel || "Selected Model";

  doc.text(model, 40, y);
  doc.text(String(quantity), 270, y);
  doc.text(`$${finalPrice.toLocaleString()}`, 330, y);
  doc.text(`$${total.toLocaleString()}`, 450, y);

  y += 40;

  // Summary Totals
  doc.setFontSize(9);
  doc.text(`Subtotal:  $${total.toLocaleString()}`, 400, y);
  y += 18;
  doc.text(`Taxes (optional):  —`, 400, y);
  y += 18;
  doc.setFont("helvetica", "bold");
  doc.text(`Total Due:  $${total.toLocaleString()}`, 400, y);
  doc.setFont("helvetica", "normal");

  // Signature line
  y += 60;
  doc.text("Authorized By:", 40, y);
  doc.line(140, y + 2, 300, y + 2);

  doc.text("Date:", 340, y);
  doc.line(380, y + 2, 460, y + 2);

  doc.save(`PO-${requestId || Date.now()}.pdf`);
}

  // -------------------------------
  // Phase Derivation (for timeline)
  // -------------------------------
  type PhaseKey = "submitted" | "scout" | "compute" | "evaluate" | "negotiate" | "finalize";

  const phaseFromMessages: PhaseKey = useMemo(() => {
    const text = messages.join("\n").toLowerCase();
    if (/savings|accepted|final price|deal complete|evaluation result delivered/.test(text)) return "finalize";
    if (/negotiator|bulk discount|tier/.test(text)) return "negotiate";
    if (/evaluator|metta|hybrid|symbolic|compute scoring complete/.test(text)) return "evaluate";
    if (/cudos|compute|queued for evaluation|dispatching batch/.test(text)) return "compute";
    if (/scout|catalog|retrieved .* laptops|found .* candidates/.test(text)) return "scout";
    if (requestId) return "submitted";
    return "submitted";
  }, [messages, requestId]);

  const phases: { key: PhaseKey; label: string }[] = useMemo(
    () => [
      { key: "submitted", label: "Submitted" },
      { key: "scout", label: "Scout" },
      { key: "compute", label: "Compute" },
      { key: "evaluate", label: "Evaluate" },
      { key: "negotiate", label: "Negotiate" },
      { key: "finalize", label: "Finalize" },
    ],
    []
  );

  const currentPhaseIndex = useMemo(
    () => phases.findIndex((p) => p.key === phaseFromMessages),
    [phases, phaseFromMessages]
  );

  // -------------------------------
  // Controls
  // -------------------------------
  async function startProcurement() {
    // Reset state
    setMessages([]);
    setScoutCount(null);
    setFinalPrice(null);
    setCompleted(false);
    setRequestId(null);

    setIsStreaming(true);

    const res = await fetch("https://pronet-0u6p.onrender.com/api/procure", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        use_case: useCase,
        quantity,
        max_budget_per_unit: budget,
      }),
    });

    const { request_id } = await res.json();
    setRequestId(request_id);
    setMessages((m) => [...m, `Request Started: ${request_id}`]);

    const streamUrl = `https://pronet-0u6p.onrender.com/api/stream/${request_id}`;
    const es = new EventSource(streamUrl);
    eventSourceRef.current = es;

    es.onmessage = (e) => {
  const parsed = parseEvent(e.data);

  switch (parsed.type) {
    case "model":
      setSelectedModel(parsed.name);
      break;
    case "scout":
      setScoutCount(parsed.count);
      break;
    case "negotiation":
      setFinalPrice(parsed.finalUnit);
      break;
    case "done":
      setCompleted(true);
      break;
    case "log":
      setMessages((m) => [...m, parsed.text]);
      break;
  }
};

    es.onerror = () => {
      setMessages((m) => [...m, "Stream closed or lost connection"]);
      es.close();
      setIsStreaming(false);
    };
  }

  function stopStream() {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
    setMessages((m) => [...m, "Stream stopped by user"]);
  }

  // -------------------------------
  // UI
  // -------------------------------
  return (
    <div className="min-h-screen bg-white">
      {/* Top Bar */}
      <header className="border-b border-slate-200">
        <div className="mx-auto max-w-6xl px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="h-8 w-8 rounded-md bg-indigo-600" aria-hidden="true" />
            <div>
              <div className="text-sm text-slate-500">Procurement</div>
              <h1 className="text-lg font-semibold text-slate-900">Multi-Agent Procurement System</h1>
            </div>
          </div>
          <nav className="text-sm text-slate-500">
            <span className="text-slate-400">Home</span> / <span>Procurement</span>
          </nav>
        </div>
      </header>

      {/* Content */}
      <main className="mx-auto max-w-6xl px-6 py-10 space-y-10">
        {/* Form + Summary */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Form Card */}
          <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl">
            <div className="px-6 py-5 border-b border-slate-200">
              <h2 className="text-base font-semibold text-slate-900">Laptop Bulk Order</h2>
              <p className="text-sm text-slate-500">Search and purchase laptops in bulk by use case, price, and RAM.</p>
            </div>
            <div className="px-6 py-6 space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700">Use case</label>
                <select
  value={useCase}
  onChange={(e) => setUseCase(e.target.value)}
  className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
>
  {USE_CASE_OPTIONS.map((uc) => (
    <option key={uc} value={uc}>
      {uc.replace(/-/g, " ")}
    </option>
  ))}
</select>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-slate-700">Quantity</label>
                  <input
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(Number(e.target.value))}
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">
                    Max budget per unit (USD)
                  </label>
                  <input
                    type="number"
                    value={budget}
                    onChange={(e) => setBudget(Number(e.target.value))}
                    className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  onClick={startProcurement}
                  disabled={isStreaming}
                  className="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-60"
                >
                  Start procurement
                </button>
                <button
                  onClick={stopStream}
                  disabled={!isStreaming}
                  className="inline-flex items-center rounded-md bg-white px-4 py-2 text-sm font-medium text-slate-700 border border-slate-300 shadow-sm hover:bg-slate-50 disabled:opacity-60"
                >
                  Stop
                </button>
                {requestId && (
                  <span className="ml-auto text-xs text-slate-500">
                    Request ID: <span className="font-mono">{requestId}</span>
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* KPIs */}
          <div className="bg-white border border-slate-200 rounded-xl">
            <div className="px-6 py-5 border-b border-slate-200">
              <h3 className="text-base font-semibold text-slate-900">Summary</h3>
            </div>
            <div className="px-6 py-6 space-y-4">
              <KPI label="Scout candidates" value={scoutCount !== null ? String(scoutCount) : "—"} />
              <KPI
    label="Final price / unit"
    value={finalPrice !== null ? `$${finalPrice.toLocaleString()}` : "—"}
  />

  {/* ✅ New Total Cost */}
  <div className="flex items-center justify-between border-t border-slate-200 pt-4">
    <div className="text-sm text-slate-700 font-medium">Total cost</div>
    <div className="text-sm font-semibold text-slate-900">
      {finalPrice !== null ? `$${(finalPrice * quantity).toLocaleString()}` : "—"}
    </div>
  </div>

  <KPI label="Status" value={completed ? "Completed" : requestId ? "In progress" : "—"} />

  {/* ✅ PDF Button */}
  <button
  onClick={generatePDF}
  disabled={!completed}
  className="mt-4 w-full inline-flex items-center justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
>
  Download Purchase Order (PDF)
</button>
</div>
          </div>
        </section>

        {/* Timeline */}
        <section className="bg-white border border-slate-200 rounded-xl">
          <div className="px-6 py-5 border-b border-slate-200">
            <h3 className="text-base font-semibold text-slate-900">Workflow</h3>
            <p className="text-sm text-slate-500">Track progress across stages.</p>
          </div>
          <div className="px-6 py-6">
            <ol className="grid grid-cols-2 md:grid-cols-6 gap-4">
              {phases.map((p, idx) => {
                const state =
                  idx < currentPhaseIndex
                    ? "done"
                    : idx === currentPhaseIndex
                    ? "active"
                    : "upcoming";
                return <PhasePill key={p.key} label={p.label} state={state} />;
              })}
            </ol>
          </div>
        </section>

        {/* Live Stream Log */}
        <section className="bg-white border border-slate-200 rounded-xl">
          <div className="px-6 py-5 border-b border-slate-200 flex items-center justify-between">
            <div>
              <h3 className="text-base font-semibold text-slate-900">Live event stream</h3>
              <p className="text-sm text-slate-500">
                Server-sent events from agents, evaluators and negotiator.
              </p>
            </div>
            <div
              className={`h-2 w-2 rounded-full ${
                isStreaming ? "bg-emerald-500" : "bg-slate-300"
              }`}
              aria-label={isStreaming ? "Streaming" : "Idle"}
            />
          </div>
          <div className="px-6 py-6">
            <div className="h-[420px] overflow-y-auto rounded-lg border border-slate-200 bg-slate-50">
              <ul className="divide-y divide-slate-200">
                {messages.length === 0 ? (
                  <li className="px-4 py-3 text-sm text-slate-500">No events yet.</li>
                ) : (
                  messages.map((msg, i) => (
                    <li key={i} className="px-4 py-3">
                      <div className="flex items-start gap-4">
                        <div className="min-w-[70px] text-xs font-mono text-slate-500 pt-0.5">
                          {String(i + 1).padStart(2, "0")}
                        </div>
                        <div className="flex-1">
                          <div className="text-sm text-slate-900 whitespace-pre-wrap">{msg}</div>
                        </div>
                      </div>
                    </li>
                  ))
                )}
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

/** Small KPI component for the right-hand summary card */
function KPI({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <div className="text-sm text-slate-600">{label}</div>
      <div className="text-sm font-medium text-slate-900">{value}</div>
    </div>
  );
}

/** Phase pill for the workflow timeline */
function PhasePill({
  label,
  state,
}: {
  label: string;
  state: "done" | "active" | "upcoming";
}) {
  const classes =
    state === "done"
      ? "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200"
      : state === "active"
      ? "bg-indigo-50 text-indigo-700 ring-1 ring-inset ring-indigo-200"
      : "bg-slate-50 text-slate-600 ring-1 ring-inset ring-slate-200";
  return (
    <li
      className={`px-3 py-2 rounded-md text-center text-xs font-medium ${classes}`}
      aria-current={state === "active" ? "step" : undefined}
    >
      {label}
    </li>
  );
}
