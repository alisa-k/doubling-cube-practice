import "./styles.css";
import { actionLabels, isPuzzle, type CubeAction, type Puzzle } from "./puzzle";

const offerActions: CubeAction[] = ["no-double", "double-take", "double-pass", "too-good"];
const responseActions: CubeAction[] = ["take", "pass"];
const progressKey = "doubling-cube-practice-progress-v1";

interface Progress {
  attempts: number;
  correct: number;
}

function readProgress(): Progress {
  try {
    const saved = localStorage.getItem(progressKey);
    return saved ? (JSON.parse(saved) as Progress) : { attempts: 0, correct: 0 };
  } catch {
    return { attempts: 0, correct: 0 };
  }
}

function saveProgress(progress: Progress): void {
  localStorage.setItem(progressKey, JSON.stringify(progress));
}

function formatEquity(value: number): string {
  return `${value >= 0 ? "+" : ""}${value.toFixed(3)}`;
}

function explanationWithoutEquities(note: string): string {
  return note.split(" Normalized equity")[0] ?? note;
}

function equityBreakdownMarkup(puzzle: Puzzle): string {
  const equities = puzzle.analysis.equities;
  if (!equities) return "";

  const isResponse = puzzle.decisionType === "response";
  const recommendation = puzzle.analysis.recommendation?.toLowerCase() ?? "";
  const opponentReply = recommendation.includes("pass")
    ? "pass"
    : recommendation.includes("take")
      ? "take"
      : null;
  const options = isResponse
    ? [
        {
          action: "take" as CubeAction,
          label: "Take",
          value: -equities.doubleTake,
          detail: "Your equity if you accept the double",
        },
        {
          action: "pass" as CubeAction,
          label: "Pass",
          value: -equities.doublePass,
          detail: "Your equity if you give up the game",
        },
      ]
    : [
        {
          action: puzzle.answer.action === "too-good" ? ("too-good" as CubeAction) : ("no-double" as CubeAction),
          label: puzzle.answer.action === "too-good" ? "Play on (too good)" : "No double",
          value: equities.noDouble,
          detail: "Equity if you keep the cube where it is",
        },
        {
          action: "double-take" as CubeAction,
          label: "Double / Take",
          value: equities.doubleTake,
          detail: "Equity if you double and opponent takes",
        },
        {
          action: "double-pass" as CubeAction,
          label: "Double / Pass",
          value: equities.doublePass,
          detail: "Equity if you double and opponent passes",
        },
      ];

  return `
    <section class="equity-breakdown" aria-labelledby="equity-title">
      <div class="equity-breakdown__heading">
        <strong id="equity-title">Equity comparison</strong>
        <span>Normalized equity · higher is better for you</span>
      </div>
      <div class="equity-options">
        ${options
          .map(
            ({ action, label, value, detail }) => {
              const isOpponentReply =
                !isResponse &&
                ((action === "double-take" && opponentReply === "take") ||
                  (action === "double-pass" && opponentReply === "pass"));
              return `
              <div class="equity-option ${action === puzzle.answer.action ? "equity-option--best" : ""}">
                <div class="equity-option__label">
                  <span>${label}</span>
                  <span class="equity-option__badges">
                    ${action === puzzle.answer.action ? '<strong class="equity-option__badge">Correct action</strong>' : ""}
                    ${isOpponentReply ? '<strong class="equity-option__badge equity-option__badge--reply">Opponent’s reply</strong>' : ""}
                  </span>
                </div>
                <output>${formatEquity(value)}</output>
                <p>${detail}</p>
              </div>
            `;
            },
          )
          .join("")}
      </div>
      ${
        isResponse
          ? '<p class="equity-breakdown__note">GNUbg stores these branches from the doubler’s perspective; they are shown here from your perspective.</p>'
          : '<p class="equity-breakdown__note">After a double, your opponent chooses their best reply. A higher hypothetical branch does not help if they would choose the other response. “Too good” uses the play-on/no-double equity.</p>'
      }
    </section>
  `;
}

function checkerMarkup(count: number, explicitOwner?: "you" | "opponent"): string {
  const owner = explicitOwner ?? (count > 0 ? "you" : "opponent");
  const amount = Math.abs(count);
  const visible = Math.min(amount, 5);
  const checkers = Array.from(
    { length: visible },
    () => `<span class="checker checker--${owner}" aria-hidden="true"></span>`,
  ).join("");
  const overflow = amount > 5 ? `<strong class="stack-count">${amount}</strong>` : "";
  return `${checkers}${overflow}`;
}

function borneOffMarkup(count: number, owner: "you" | "opponent"): string {
  return Array.from(
    { length: count },
    () => `<span class="borne-off-checker borne-off-checker--${owner}" aria-hidden="true"></span>`,
  ).join("");
}

function pointMarkup(puzzle: Puzzle, point: number, direction: "up" | "down"): string {
  const count = puzzle.board.points[point - 1] ?? 0;
  const label =
    count === 0
      ? "empty"
      : `${Math.abs(count)} ${count > 0 ? "of your white" : "opponent black"} checkers`;
  return `
    <div class="point point--${direction}" aria-label="Point ${point}, ${label}">
      <span class="point__number">${point}</span>
      <span class="point__checkers">${checkerMarkup(count)}</span>
    </div>
  `;
}

function boardMarkup(puzzle: Puzzle): string {
  const upperLeft = Array.from({ length: 6 }, (_, index) => pointMarkup(puzzle, index + 13, "down")).join("");
  const upperRight = Array.from({ length: 6 }, (_, index) => pointMarkup(puzzle, index + 19, "down")).join("");
  const lowerLeft = Array.from({ length: 6 }, (_, index) => pointMarkup(puzzle, 12 - index, "up")).join("");
  const lowerRight = Array.from({ length: 6 }, (_, index) => pointMarkup(puzzle, 6 - index, "up")).join("");
  const [youOnBar, opponentOnBar] = puzzle.board.bar;
  const [youOff, opponentOff] = puzzle.board.off;

  return `
    <section class="board" aria-label="Backgammon position. You are White; opponent is Black.">
      <div class="board__quadrant board__quadrant--upper-left">${upperLeft}</div>
      <div class="board__quadrant board__quadrant--upper-right">${upperRight}</div>
      <div class="board__quadrant board__quadrant--lower-left">${lowerLeft}</div>
      <div class="board__quadrant board__quadrant--lower-right">${lowerRight}</div>

      <div class="board__bar" aria-label="Bar: ${youOnBar} of your white checkers and ${opponentOnBar} black checkers">
        <span class="board__rail-label" aria-hidden="true">Bar</span>
        <div class="board__bar-slot board__bar-slot--opponent">${checkerMarkup(opponentOnBar, "opponent")}</div>
        <div class="board__bar-slot board__bar-slot--you">${checkerMarkup(youOnBar, "you")}</div>
      </div>

      <div class="board__off" aria-label="Borne off: ${youOff} of your white checkers and ${opponentOff} black checkers">
        <span class="board__rail-label" aria-hidden="true">Off</span>
        <div class="board__off-slot board__off-slot--opponent">${borneOffMarkup(opponentOff, "opponent")}</div>
        <div class="board__off-slot board__off-slot--you">${borneOffMarkup(youOff, "you")}</div>
      </div>
    </section>
  `;
}

function render(puzzles: Puzzle[], puzzleIndex: number): void {
  const app = document.querySelector<HTMLElement>("#app");
  if (!app) throw new Error("App root not found");

  const puzzle = puzzles[puzzleIndex];
  const progress = readProgress();
  const score = progress.attempts === 0 ? "—" : `${Math.round((progress.correct / progress.attempts) * 100)}%`;
  const matchLabel = puzzle.match.length === 0 ? "Money game" : `${puzzle.match.length}-point match`;
  const [yourMatchScore, opponentMatchScore] = puzzle.match.score;
  const isResponse = puzzle.decisionType === "response";
  const actions = isResponse ? responseActions : offerActions;
  const cubeLabel = isResponse
    ? `Opponent doubled: cube ${puzzle.match.cubeValue} → ${puzzle.match.offeredCubeValue ?? puzzle.match.cubeValue * 2}`
    : `Cube ${puzzle.match.cubeValue}, ${puzzle.match.cubeOwner}`;
  const decisionCue = isResponse ? "White (you) · Responding to a double" : "White (you) · On roll";
  const decisionQuestion = isResponse ? "Do you take or pass?" : "What is the correct cube action?";
  const decisionContext = isResponse
    ? '<p class="decision-context">Your opponent offered the double. This take/pass decision is yours.</p>'
    : "";
  const scoreMarkup =
    puzzle.match.length === 0
      ? ""
      : `
        <div class="match-score" role="group" aria-label="Match score: you, White, ${yourMatchScore} ${yourMatchScore === 1 ? "point" : "points"}; opponent, Black, ${opponentMatchScore} ${opponentMatchScore === 1 ? "point" : "points"}">
          <div class="match-score__side match-score__side--you">
            <span class="color-dot color-dot--white" aria-hidden="true"></span>
            <span class="match-score__identity"><strong>You</strong><span>White</span></span>
          </div>
          <div class="match-score__result" aria-hidden="true">
            <strong><span>${yourMatchScore}</span><span class="match-score__dash">–</span><span>${opponentMatchScore}</span></strong>
            <span>Current score</span>
          </div>
          <div class="match-score__side match-score__side--opponent">
            <span class="match-score__identity"><strong>Opponent</strong><span>Black</span></span>
            <span class="color-dot color-dot--black" aria-hidden="true"></span>
          </div>
        </div>
      `;
  const nextPuzzleIndex = (puzzleIndex + 1) % puzzles.length;
  const nextLabel = puzzleIndex === puzzles.length - 1 ? "Start over" : "Next puzzle";

  app.innerHTML = `
    <header class="header">
      <div>
        <h1>Doubling Cube Practice</h1>
      </div>
      <dl class="score" aria-label="Practice progress">
        <div><dt>Attempts</dt><dd id="attempt-count">${progress.attempts}</dd></div>
        <div><dt>Accuracy</dt><dd id="accuracy-score">${score}</dd></div>
      </dl>
    </header>

    <section class="position-card">
      <div class="position-meta">
        <span>${matchLabel}</span>
        <span class="${isResponse ? "cube-offer" : ""}">${cubeLabel}</span>
      </div>
      ${scoreMarkup}
      ${boardMarkup(puzzle)}
    </section>

    <section class="decision-card">
      <p class="eyebrow eyebrow--player"><span class="color-dot color-dot--white" aria-hidden="true"></span>${decisionCue}</p>
      <h2>${decisionQuestion}</h2>
      ${decisionContext}
      <div class="actions ${isResponse ? "actions--response" : ""}">
        ${actions.map((action) => `<button type="button" data-action="${action}">${actionLabels[action]}</button>`).join("")}
      </div>
      <div id="feedback" class="feedback" aria-live="polite"></div>
    </section>

    <footer>
      Puzzle ${puzzleIndex + 1} of ${puzzles.length} · ${puzzle.source} · ${puzzle.analysis.engine}
    </footer>
  `;

  const feedback = document.querySelector<HTMLElement>("#feedback");
  const buttons = document.querySelectorAll<HTMLButtonElement>("[data-action]");

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const selected = button.dataset.action as CubeAction;
      const correct = selected === puzzle.answer.action;
      const nextProgress = {
        attempts: progress.attempts + 1,
        correct: progress.correct + (correct ? 1 : 0),
      };

      saveProgress(nextProgress);
      const attemptCount = document.querySelector<HTMLElement>("#attempt-count");
      const accuracyScore = document.querySelector<HTMLElement>("#accuracy-score");
      if (attemptCount) attemptCount.textContent = String(nextProgress.attempts);
      if (accuracyScore) {
        accuracyScore.textContent = `${Math.round((nextProgress.correct / nextProgress.attempts) * 100)}%`;
      }
      buttons.forEach((choice) => {
        choice.disabled = true;
        if (choice.dataset.action === puzzle.answer.action) choice.classList.add("correct");
      });
      if (!correct) button.classList.add("incorrect");

      if (feedback) {
        feedback.innerHTML = `
          <div class="feedback__summary">
            <strong>${correct ? "Correct." : `Answer: ${actionLabels[puzzle.answer.action]}.`}</strong>
            <span>${explanationWithoutEquities(puzzle.answer.note)}</span>
          </div>
          ${equityBreakdownMarkup(puzzle)}
          <div class="feedback__actions">
            <button type="button" class="reset">${nextLabel}</button>
          </div>
        `;
        feedback
          .querySelector<HTMLButtonElement>(".reset")
          ?.addEventListener("click", () => render(puzzles, nextPuzzleIndex));
      }
    });
  });
}

async function start(): Promise<void> {
  const response = await fetch(`${import.meta.env.BASE_URL}puzzles.json`);
  if (!response.ok) throw new Error("Could not load puzzle data");

  const data: unknown = await response.json();
  if (!Array.isArray(data) || data.length === 0 || !data.every(isPuzzle)) {
    throw new Error("Puzzle data is invalid");
  }

  render(data, 0);
}

start().catch((error: unknown) => {
  const app = document.querySelector<HTMLElement>("#app");
  if (app) {
    app.innerHTML = `<p class="fatal-error">${error instanceof Error ? error.message : "The app could not start."}</p>`;
  }
});

