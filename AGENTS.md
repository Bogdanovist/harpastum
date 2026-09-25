# Harpastum

A sports management sim set in the Roman world, built on the ancient ball
game harpastum. The player coaches a team of one people (Romans, Greeks,
Celts and others), sets tactics and formations, and watches a match
simulation play them out.

`context/index.md` holds the glossary, the repo's records and the open
projects. Read it before you change code.

## Current state

The game design is open. The code is a throwaway web prototype for finding
the design: Vite, React and TypeScript, played in a phone browser. Speed of
iteration beats code quality. A production stack will be chosen once the game
is known.

The match simulation lives in `src/sim/`, apart from React and the canvas.
It advances in fixed steps, and a match replays exactly from its seed. Code
in `src/sim/` draws every random number from `nextRandom` and never reads
`Math.random` or the wall clock, or seeded replays and the tests break.

`legacy/` holds the match AI written in Python in 2013: player roles,
steering, move states, threat assessment and a message bus. It does not run,
because `legacy/Pitch.py` imports a `Helper` module that is not in the repo.
Read it as a reference for the match simulation. Do not build on it.

## Running the app

- `npm install`, then `npm run dev`. The dev server uses port 5174. The Flux
  `phone-prototype` skill says how to serve it to Matt's phone and what to do
  when the port is taken.
- Checks: `npm test` (Vitest), `npm run build` (type-check and bundle),
  `npm run lint` (oxlint).
