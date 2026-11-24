export type CubeAction =
  | "no-double"
  | "double-take"
  | "double-pass"
  | "too-good"
  | "take"
  | "pass";

export interface MatchState {
  length: number;
  score: [number, number];
  cubeValue: number;
  offeredCubeValue?: number;
  cubeOwner: "centered" | "you" | "opponent";
}

export interface Puzzle {
  id: string;
  source: string;
  positionId: string | null;
  matchId: string | null;
  decisionType: "offer" | "response";
  playerOnRoll: "you" | "opponent";
  match: MatchState;
  board: {
    points: number[];
    /** Tuple order is [you, opponent]. */
    bar: [number, number];
    /** Tuple order is [you, opponent]. */
    off: [number, number];
  };
  answer: {
    action: CubeAction;
    note: string;
  };
  analysis: {
    engine: string;
    method: string;
    recommendation?: string;
    offerRecommendation?: string;
    equities?: {
      optimal: number;
      noDouble: number;
      doubleTake: number;
      doublePass: number;
      unit: string;
    };
    settings?: {
      plies: number;
      cubeful: boolean;
      pruning: boolean;
      deterministic: boolean;
      noise: number;
    };
  };
  provenance?: {
    sourceFile: string;
    game: number;
    record: number;
    player: "X" | "O";
    doubler?: "X" | "O";
  };
  tags: string[];
}

export const actionLabels: Record<CubeAction, string> = {
  "no-double": "No double",
  "double-take": "Double / Take",
  "double-pass": "Double / Pass",
  "too-good": "Too good",
  take: "Take",
  pass: "Pass",
};

export function isPuzzle(value: unknown): value is Puzzle {
  if (typeof value !== "object" || value === null) return false;

  const candidate = value as Partial<Puzzle>;
  return (
    typeof candidate.id === "string" &&
    (candidate.decisionType === "offer" || candidate.decisionType === "response") &&
    Array.isArray(candidate.board?.points) &&
    candidate.board.points.length === 24 &&
    typeof candidate.answer?.action === "string" &&
    candidate.answer.action in actionLabels
  );
}

