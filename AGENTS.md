# Doubling Cube Practice

## Goal

Build a lightweight, local-first app for practicing backgammon cube decisions.

## Project rules

- Keep the browser app framework-free unless the UI genuinely outgrows native TypeScript.
- Do not add a backend, account system, or cloud database without an explicit product need.
- Keep GNU Backgammon and `.mat` processing in an offline generation pipeline; the browser reads generated puzzle data.
- Preserve analysis provenance for every generated puzzle: source, GNUbg version, settings, and rollout details when available.
- Treat files under `data/matches/` as private local inputs and do not commit them.
- Prefer accessible HTML controls and keyboard-friendly interactions.

## Commands

- `npm run dev` — start the local development server.
- `npm run build` — type-check and build the static app.
- `npm run preview` — preview the production build locally.
- `./scripts/gnubg --version` — verify the project-local GNUbg installation.
- `./scripts/gnubg --tty` — start GNUbg's command-line interface.

## Verification

Run `npm run build` after code changes.

