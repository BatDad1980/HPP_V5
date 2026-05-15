import { useMemo, useState } from "react";
import {
  Activity,
  ArrowRight,
  Brain,
  Check,
  CircleAlert,
  Compass,
  Database,
  Dumbbell,
  Flame,
  Gauge,
  LineChart,
  Moon,
  RotateCcw,
  Shield,
  Sparkles,
  Timer,
} from "lucide-react";
import { protocols } from "./protocols";
import type { Mode, Protocol, RunEntry, Signals, MaturityStage } from "./types";

const STORAGE_KEY = "hpp-v5-runs";

type PowerMode = "battery" | "plugged" | "demo";

const defaultSignals: Signals = {
  energy: 54,
  focus: 42,
  mood: 56,
  stress: 38,
  clarity: 45,
  tension: 33,
};

const signalLabels: Array<[keyof Signals, string]> = [
  ["energy", "Energy"],
  ["focus", "Focus"],
  ["mood", "Mood"],
  ["stress", "Stress"],
  ["clarity", "Clarity"],
  ["tension", "Tension"],
];

const habitMemoryEvidence = {
  threshold: "14",
  recallGain: "12.74x",
  matureGain: "89.63x",
  device: "RTX 4050",
};

function loadRuns(): RunEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveRuns(runs: RunEntry[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(runs));
}

function stageForCount(count: number): MaturityStage {
  if (count >= 28) return "Guardian";
  if (count >= 14) return "Myelinated";
  if (count >= 8) return "Scaffold";
  if (count >= 3) return "Nurture";
  return "Seed";
}

function signalDelta(before: Signals, after: Signals) {
  return Math.round(
    (after.energy - before.energy +
      after.focus - before.focus +
      after.mood - before.mood +
      after.clarity - before.clarity -
      (after.stress - before.stress) -
      (after.tension - before.tension)) /
      6,
  );
}

function App() {
  const [runs, setRuns] = useState<RunEntry[]>(loadRuns);
  const [selectedId, setSelectedId] = useState(protocols[0].id);
  const [before, setBefore] = useState<Signals>(defaultSignals);
  const [after, setAfter] = useState<Signals>({
    ...defaultSignals,
    stress: 28,
    focus: 50,
    clarity: 52,
  });
  const [reflection, setReflection] = useState("");
  const [resistance, setResistance] = useState(32);
  const [activeStep, setActiveStep] = useState(0);
  const [powerMode, setPowerMode] = useState<PowerMode>("battery");

  const selected = protocols.find((protocol) => protocol.id === selectedId) ?? protocols[0];

  const protocolRuns = runs.filter((run) => run.protocolId === selected.id);
  const selectedStage = stageForCount(protocolRuns.length);
  const latest = runs[0];

  const mode: Mode = before.stress > 72 || before.tension > 70 ? "sentinel" : selected.mode;

  const recentScore = useMemo(() => {
    if (!runs.length) return 0;
    const recent = runs.slice(0, 7).map((run) => signalDelta(run.before, run.after));
    return Math.round(recent.reduce((total, score) => total + score, 0) / recent.length);
  }, [runs]);

  const stabilizedCount = useMemo(
    () => protocols.filter((protocol) => runs.filter((run) => run.protocolId === protocol.id).length >= 14).length,
    [runs],
  );

  const updateSignal = (target: "before" | "after", key: keyof Signals, value: number) => {
    const setter = target === "before" ? setBefore : setAfter;
    setter((current) => ({ ...current, [key]: value }));
  };

  const completeRun = () => {
    const now = new Date().toISOString();
    const entry: RunEntry = {
      id: crypto.randomUUID(),
      protocolId: selected.id,
      protocolName: selected.name,
      startedAt: now,
      completedAt: now,
      before,
      after,
      reflection: reflection.trim() || selected.reflectionPrompt,
      resistance,
      mode,
    };
    const nextRuns = [entry, ...runs];
    setRuns(nextRuns);
    saveRuns(nextRuns);
    setReflection("");
    setActiveStep(0);
    setBefore(after);
    setAfter({
      ...after,
      focus: Math.min(100, after.focus + 4),
      clarity: Math.min(100, after.clarity + 3),
      stress: Math.max(0, after.stress - 3),
    });
  };

  const resetEvidence = () => {
    setRuns([]);
    saveRuns([]);
  };

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Hyperplasticity Protocol V5</p>
          <h1>Train the state. Rewrite the loop.</h1>
        </div>
        <div className={`mode-pill ${mode}`}>
          {mode === "sentinel" ? <Shield size={18} /> : <Sparkles size={18} />}
          {mode === "sentinel" ? "Sentinel" : "Nurture"}
        </div>
      </header>

      <section className="command-grid">
        <aside className="left-rail">
          <div className="identity-panel">
            <div>
              <p className="label">Active Identity</p>
              <h2>Signal Architect</h2>
            </div>
            <Brain size={28} />
          </div>

          <div className="metric-stack">
            <Metric icon={<Gauge size={18} />} label="Recent shift" value={`${recentScore > 0 ? "+" : ""}${recentScore}`} />
            <Metric icon={<Flame size={18} />} label="Habit-14" value={`${Math.min(protocolRuns.length, 14)}/14`} />
            <Metric icon={<Database size={18} />} label="Evidence" value={`${runs.length}`} />
            <Metric icon={<Shield size={18} />} label="Stable loops" value={`${stabilizedCount}`} />
          </div>

          <div className="stage-panel">
            <p className="label">Selected Loop</p>
            <div className="stage-row">
              <span>{selectedStage}</span>
              <span>{protocolRuns.length} runs</span>
            </div>
            <div className="habit-track" aria-label="Habit 14 progress">
              {Array.from({ length: 14 }, (_, index) => (
                <span key={index} className={index < Math.min(protocolRuns.length, 14) ? "filled" : ""} />
              ))}
            </div>
          </div>

          <div className="power-panel">
            <p className="label">Power Mode</p>
            <div className="power-options">
              <button className={powerMode === "battery" ? "active" : ""} onClick={() => setPowerMode("battery")}>
                Battery
              </button>
              <button className={powerMode === "plugged" ? "active" : ""} onClick={() => setPowerMode("plugged")}>
                Plugged
              </button>
              <button className={powerMode === "demo" ? "active" : ""} onClick={() => setPowerMode("demo")}>
                Demo
              </button>
            </div>
            <p className="power-note">
              {powerMode === "battery" && "Light work only. No training or GPU-heavy loops."}
              {powerMode === "plugged" && "CUDA work allowed with explicit device checks."}
              {powerMode === "demo" && "Buyer-safe outputs, sanitized evidence, deterministic flow."}
            </p>
          </div>
        </aside>

        <section className="workbench">
          <div className="section-head">
            <div>
              <p className="label">Today</p>
              <h2>{selected.name}</h2>
            </div>
            <div className="duration">
              <Timer size={18} />
              {selected.duration}
            </div>
          </div>

          <div className="protocol-strip">
            {protocols.map((protocol) => (
              <button
                className={protocol.id === selected.id ? "protocol-tab active" : "protocol-tab"}
                key={protocol.id}
                onClick={() => {
                  setSelectedId(protocol.id);
                  setActiveStep(0);
                }}
              >
                {protocol.mode === "sentinel" ? <CircleAlert size={16} /> : <Compass size={16} />}
                <span>{protocol.name}</span>
              </button>
            ))}
          </div>

          <div className="run-grid">
            <div className="signal-panel">
              <div className="mini-head">
                <h3>Before</h3>
                <Activity size={18} />
              </div>
              <SignalSliders values={before} target="before" onChange={updateSignal} />
            </div>

            <div className="protocol-card">
              <p className="intent">{selected.intent}</p>
              <p className="trigger">{selected.trigger}</p>
              <div className="step-list">
                {selected.steps.map((step, index) => (
                  <button
                    className={index === activeStep ? "step active" : index < activeStep ? "step done" : "step"}
                    key={step}
                    onClick={() => setActiveStep(index)}
                  >
                    <span>{index < activeStep ? <Check size={15} /> : index + 1}</span>
                    {step}
                  </button>
                ))}
              </div>
              <button className="advance" onClick={() => setActiveStep((step) => Math.min(selected.steps.length, step + 1))}>
                Advance loop <ArrowRight size={18} />
              </button>
            </div>

            <div className="signal-panel">
              <div className="mini-head">
                <h3>After</h3>
                <LineChart size={18} />
              </div>
              <SignalSliders values={after} target="after" onChange={updateSignal} />
            </div>
          </div>

          <div className="reflection-row">
            <label>
              <span>Reflection</span>
              <textarea
                value={reflection}
                onChange={(event) => setReflection(event.target.value)}
                placeholder={selected.reflectionPrompt}
              />
            </label>
            <label className="resistance">
              <span>Resistance</span>
              <input
                type="range"
                min="0"
                max="100"
                value={resistance}
                onChange={(event) => setResistance(Number(event.target.value))}
              />
              <strong>{resistance}</strong>
            </label>
            <button className="complete" onClick={completeRun}>
              Save evidence <Check size={18} />
            </button>
          </div>
        </section>

        <aside className="right-rail">
          <div className="insight-panel">
            <div className="mini-head">
              <h3>Pattern</h3>
              <Moon size={18} />
            </div>
            {latest ? (
              <>
                <p className="large-delta">{signalDelta(latest.before, latest.after) >= 0 ? "+" : ""}{signalDelta(latest.before, latest.after)}</p>
                <p>{latest.protocolName}</p>
                <small>{new Date(latest.completedAt).toLocaleString()}</small>
              </>
            ) : (
              <>
                <p className="large-delta">0</p>
                <p>No saved loops yet.</p>
                <small>First evidence lands here.</small>
              </>
            )}
          </div>

          <div className="evidence-panel">
            <div className="mini-head">
              <h3>Habit Memory</h3>
              <Dumbbell size={18} />
            </div>
            <div className="evidence-grid">
              <span>
                <small>Lock</small>
                <strong>{habitMemoryEvidence.threshold}</strong>
              </span>
              <span>
                <small>Recall</small>
                <strong>{habitMemoryEvidence.recallGain}</strong>
              </span>
              <span>
                <small>Mature</small>
                <strong>{habitMemoryEvidence.matureGain}</strong>
              </span>
              <span>
                <small>Device</small>
                <strong>{habitMemoryEvidence.device}</strong>
              </span>
            </div>
            <p>Repeated practice behaves like protected muscle memory under noise.</p>
          </div>

          <div className="history-panel">
            <div className="mini-head">
              <h3>Evidence Log</h3>
              <button className="icon-button" onClick={resetEvidence} aria-label="Clear evidence log">
                <RotateCcw size={16} />
              </button>
            </div>
            <div className="history-list">
              {runs.slice(0, 7).map((run) => (
                <article key={run.id}>
                  <span className={`dot ${run.mode}`} />
                  <div>
                    <strong>{run.protocolName}</strong>
                    <p>{run.reflection}</p>
                  </div>
                  <b>{signalDelta(run.before, run.after) >= 0 ? "+" : ""}{signalDelta(run.before, run.after)}</b>
                </article>
              ))}
            </div>
          </div>
        </aside>
      </section>
    </main>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="metric">
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SignalSliders({
  values,
  target,
  onChange,
}: {
  values: Signals;
  target: "before" | "after";
  onChange: (target: "before" | "after", key: keyof Signals, value: number) => void;
}) {
  return (
    <div className="sliders">
      {signalLabels.map(([key, label]) => (
        <label key={key}>
          <span>{label}</span>
          <input
            type="range"
            min="0"
            max="100"
            value={values[key]}
            onChange={(event) => onChange(target, key, Number(event.target.value))}
          />
          <b>{values[key]}</b>
        </label>
      ))}
    </div>
  );
}

export default App;
