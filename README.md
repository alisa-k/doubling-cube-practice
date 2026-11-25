# Doubling Cube Practice

A deliberately small, local-first backgammon doubling-cube trainer.

## Start the app

```sh
npm install
npm run dev
```

The terminal will print the local URL to open in a browser.

## Deploy with GitHub Pages

The repository includes a GitHub Actions workflow that builds and deploys the
static app whenever `main` is pushed. In the GitHub repository settings, choose
**Pages → Build and deployment → GitHub Actions** as the publishing source.

Vite bundles the first puzzles with the app and publishes the rest in small
batches that load as needed. Private `.mat` inputs, GNUbg analysis intermediates,
and the project-local GNUbg installation remain ignored and are not deployed.

## Current architecture

- Native TypeScript and DOM APIs
- Vite for the local development server and production build
- Static puzzle data in `public/puzzles.json`
- Browser `localStorage` for practice progress
- No frontend framework, backend, account, or database

The current pilot set contains twelve real cube decisions extracted from one of
the downloaded Allgammon matches: eight decisions about whether to offer the
cube and four responses where the opponent has doubled (two takes and two
passes).

## Local GNU Backgammon engine

GNU Backgammon 1.08.003 is installed as a project-local, command-line-only tool
under `.tools/gnubg/`. The installation is ignored by Git and was built from
the official GNU source archive without the GUI. Embedded Python is enabled so
the offline generator can read GNUbg's structured match and analysis data.

Run it through the project launcher so preferences stay inside the ignored `.tools/` directory:

```sh
./scripts/gnubg --version
./scripts/gnubg --tty
```

The engine can import the downloaded Allgammon `.mat` files. The generator
removes Allgammon's extra `Crawford game` marker before import; GNUbg infers the
Crawford state from the match score and rules.

## Generate the pilot puzzles

```sh
npm run puzzles
```

This command normalizes the selected private `.mat` file, analyzes its cube
decisions at deterministic cubeful 2-ply, saves private intermediates under
`data/generated/`, and rewrites `public/puzzles.json` with the curated pilot
set. It requires the project-local GNUbg installation and the source match at
the path recorded in `scripts/extract-puzzles.py`.

## Generate every recorded cube decision

```sh
npm run puzzles:all
```

This scans the 300 private Allgammon `.mat` files, evaluates every recorded
double at deterministic cubeful 2-ply, and emits both the offer decision and
the corresponding take/pass response. Progress is checkpointed under the
ignored `data/generated/` directory. Raw match files remain local; only the
derived browser puzzle records are written to `public/puzzles.json`.

## Puzzle pipeline

```text
data/matches/*.mat
        ↓
normalization + GNU Backgammon analysis
        ↓
puzzle selection or all recorded cube decisions
        ↓
public/puzzles.json
        ↓
browser practice app
```

Raw match exports under `data/matches/` and analysis intermediates under
`data/generated/` are ignored by Git.

Each generated puzzle retains its GNUbg Position ID, Match ID, recommended
action, alternative equities, engine settings, and source provenance. Close
positions are still 2-ply results; deeper rollout screening is the next quality
step before treating this as a finished training corpus.

