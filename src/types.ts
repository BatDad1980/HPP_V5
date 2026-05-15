export type Mode = "nurture" | "sentinel";

export type MaturityStage = "Seed" | "Nurture" | "Scaffold" | "Myelinated" | "Guardian";

export type Signals = {
  energy: number;
  focus: number;
  mood: number;
  stress: number;
  clarity: number;
  tension: number;
};

export type Protocol = {
  id: string;
  name: string;
  intent: string;
  mode: Mode;
  duration: string;
  trigger: string;
  steps: string[];
  reflectionPrompt: string;
  tags: string[];
};

export type RunEntry = {
  id: string;
  protocolId: string;
  protocolName: string;
  startedAt: string;
  completedAt: string;
  before: Signals;
  after: Signals;
  reflection: string;
  resistance: number;
  mode: Mode;
};
