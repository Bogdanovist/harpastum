# Harpastum

A sports management sim set in the Roman world, built on the ancient ball
game harpastum. The player coaches a team of one people (Romans, Greeks,
Celts and others), sets tactics and formations, and watches a match
simulation play them out.

## Current state

The game design is open. The code is a throwaway web prototype for finding
the design: Vite, React and TypeScript, played in a phone browser. Speed of
iteration beats code quality. A production stack will be chosen once the game
is known.

`legacy/` holds the match AI written in Python in 2013: player roles,
steering, move states, threat assessment and a message bus. It does not run,
because `legacy/Pitch.py` imports a `Helper` module that is not in the repo.
Read it as a reference for the match simulation. Do not build on it.

## Running the app

- `npm install`, then `npm run dev`. The dev server listens on all interfaces
  at port 5174 and refuses to start if the port is taken, so the phone's URL
  stays fixed. Lines On Maps uses 5173, so both can run at once.
- Matt plays the prototype on his phone at `http://matt-human:5174`, over
  Tailscale. Each saved edit reaches the phone through hot reload, with no
  manual refresh.
- After changing code, start the dev server from your own worktree, so the
  phone shows the branch under work. Run it as a background task that your
  session can stop, and stop it when your session ends. One dev server runs
  at a time.
- If port 5174 is taken, `lsof -t -iTCP:5174 -sTCP:LISTEN` gives the process
  ID. If you cannot stop that process, ask Matt to stop it.
- Checks: `npm test` (Vitest), `npm run build` (type-check and bundle),
  `npm run lint` (oxlint).
