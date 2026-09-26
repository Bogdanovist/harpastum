---
started: 2026-09-25
---

## Why

Harpastum is a management sim. The player sets up a team and then watches a
match simulation play it out, so the simulation is the core of the game. The
design of that simulation is open. Matt needs a match he can watch on his
phone before he can judge what the game should be, and each later design
question (roles, tactics, fighting) needs a running match to try it in.

The game is contact football with almost no rules, in the style of calcio
storico in Florence. Each team tries to carry the ball into the opponent's
end zone, as in American football. There is no offside. Any player may
tackle, block or fight any opponent at any time, with or without the ball.

This project ends when Matt opens `http://matt-human:5174` on his phone and
watches an 11-a-side match play itself out: players run, pass, tackle and
fight, teams score, and the match ends on a clock. The graphics are
placeholder 8-bit pixel art.

## What exists (measured 2026-09-25)

- The `harpastum` repo serves a stub title screen (`src/TitleScreen.tsx`)
  with Vite, React and TypeScript. The archived plan
  `projects/archive/harpastum-mvp/plan.md` in the Flux repo, at Flux commit
  `63a897d`, records that setup.
- `legacy/` holds the 2013 Python match AI, which does not run. It gives
  each role a table that maps the ball's state (loose, flying, carried, own
  team attacking, own team defending) to a behaviour. The ball carrier
  passes when the nearest threat to it is worse than the threat to its best
  receiver (`legacy/Player.py`, `legacy/Threat.py`). The pitch is 100 × 50.

## Approach

### Simulation and renderer are separate

`src/sim/` is plain TypeScript with no React and no canvas. It advances the
match in fixed steps of 1/20 s, and all randomness comes from one seeded
random number generator. The renderer reads the match state each frame and
draws it.

Consequence: a match is fully set by its seed. A bug seen on the phone can be
replayed on the laptop from the seed shown on screen, and Vitest can run a
whole match in milliseconds and assert on its result (for example, that a
seed produces at least one score). The cost is that the sim must never read
the clock or `Math.random`.

The sim is a fresh TypeScript design. It borrows two ideas from `legacy/`:
the role table keyed by ball state, and the threat score for the pass
decision. It does not port the steering, move-state or message-bus code.

### Pitch and match flow

- The pitch is 100 × 50 units with an 8-unit end zone at each end, the size
  the 2013 code used for 11-a-side. A smaller pitch crowds 22 players and
  leaves runners no space to break into.
- The match starts with the ball at the centre and both teams in their own
  half. After a score, the teams reset and the team that conceded gets the
  ball at the centre.
- A match lasts 3 minutes of real time at normal speed. The score and clock
  show at the top of the screen.

### Players and roles (11 a side)

Each player has a speed and a strength. A player who is knocked down lies
prone for a few seconds, then stands up.

| Role | Count | Own team has the ball | Opponent has the ball |
|---|---|---|---|
| Brawler | 5 | The line: runs ahead of the carrier and blocks the nearest opponent in its path | Pushes through the opposing line toward the carrier |
| Runner | 3 | Finds open space toward the end zone as a pass target | Marks a receiver, and tackles a carrier who comes near |
| Centre | 1 | Starts with the ball; runs, and passes when a runner is less threatened | Linebacker: goes for the carrier |
| Back | 2 | Trails the carrier as a pass outlet | Safety: stays deep and tackles a carrier who breaks through |

When the ball is loose, the nearest players on each team chase it. When it
is in the air, the nearest players run to where it will land.

### Players decide alone

Each player chooses its own action from the match state as it sees it: the
positions of all players, the ball, and the possession state (own team,
opponent, contested, and whether the carrier is under pressure). A player
cannot see what a teammate has decided, and no team-level logic assigns
jobs. Each player carries seeded random tendencies, so two teammates in the
same spot can choose differently.

Consequence: coordination is emergent. Two teammates will at times both go
for the carrier, or both hold back, as real players do. The team looks less
drilled than it would under a shared job assignment.

### Contact

- **Tackle.** A player who reaches the carrier makes a strength contest,
  weighted by random chance. The winner stays up. If the tackler wins, the
  carrier goes down and the ball comes loose where it fell. There are no
  downs: play never stops except after a score.
- **Shoving contest.** A player who reaches an opponent without the ball
  can engage it; holding, punching and gouging are all part of it. The
  pair locks and pushes along the line between them. In each step, strength
  and a random roll decide who gains ground, so the pair moves back and
  forth. Each player has a balance that drains as it loses ground, and the
  player whose balance runs out falls. A typical contest lasts 2–5 seconds.
  A defender that gains enough ground breaks free and can go for the
  carrier. A player in a contest cannot tackle or catch.
- **Pass.** The carrier may throw in any direction. The ball flies in a
  straight line along the ground plane at a fixed speed. Any player, either
  team, within reach of it as it passes may catch it, except in its first
  2 units of flight: a defender pressed against the carrier cannot block
  the throw as it leaves the hand. A throw nobody catches lands loose.

### Screen

The match draws to a `<canvas>` at a low resolution (the pitch at 4 pixels
per unit is 400 × 200), scaled up to the phone width with smoothing off, so
it reads as 8-bit. On a phone in portrait the pitch runs top to bottom.
Players are 8 × 8 sprites drawn in code, in two team colours, with a
different shape per role and a flat, lying pose when knocked down. There are
no image files.

The title screen's button opens the match. The match screen has three
controls: pause, speed (1×, 2×, 4×) and new match (a new seed). The seed
shows under the score.

### Slices

Each slice is one PR in a worktree, shown on the phone before it merges.

1. **Players run and score.** Merged as Bogdanovist/harpastum#2.
2. **Roles, fights and passes.** Merged as Bogdanovist/harpastum#4.
3. **11-a-side, and passes you can see.** The 100 × 50 pitch, eleven
   players with the back role, the 2-unit catch-free release, and a larger
   ball in the air drawn on an arc.
4. **Shoving contests** in place of fights.
5. **Players decide alone from the game state.** The possession state,
   seeded tendencies per player, and a defence that keeps players deep.

## Decisions (Matt, 2026-09-25)

1. **Seeded, fixed-step sim separate from the screen.** Matches replay from
   a seed and are testable. Every random choice must go through the sim's
   generator.
2. **Pitch 100 × 50 with 8-unit end zones, drawn top to bottom in
   portrait** (2026-09-26, replacing 60 × 30 for 5-a-side).
3. **A tackle knocks the carrier down and the ball comes loose. No downs.**
   The alternative, a tackle that stops play for a restart like American
   football, gives a set-play game and more to design later.
4. **Passes in any direction, catchable by either team.**
5. **Shoving contests that move back and forth and end in a fall or a
   break-through** (2026-09-26). Knock-downs last seconds. There are no
   injuries and no send-offs.
6. **Eleven a side: 5 brawlers, 3 runners, 1 centre, 2 backs, with the
   behaviours in the table** (2026-09-26).
7. **A 3-minute match, watch-only, with pause, speed and new match.**
8. **Each player decides alone, with seeded random tendencies, and no
   team-level job assignment** (2026-09-26). Matt wants teammates to
   double up or both hold back at times.
9. **Passes cannot be caught in their first 2 units of flight**
   (2026-09-26).

## Out of scope

- Team selection, tactics, formations and player attributes set by the
  player.
- Communication between players.
- Injuries, fatigue, stamina and discipline.
- Any management screen, season or league.
- Sound, and real art assets.
- Any port of the Python code in `legacy/`.

## Progress

- 2026-09-25: slice 1 merged as Bogdanovist/harpastum#2 (`44f7c26`). Matt
  watched it in the browser and waived the diff review, because the code is
  prototype code. Across seeds 1–10 a match has 11 to 18 scores and about 90
  fumbles, which Matt judged acceptable for a proof of concept. The red end
  zone renders olive, because its tint blends with the grass. Matt will
  tune the match in a later session.
- 2026-09-26: slice 2 merged as Bogdanovist/harpastum#4 (`8af59f2`).
  Across seeds 1–10 a match has 61 to 70 throws, of which 20 to 35 are
  intercepted, 67 to 82 fights, and 12 to 31 fumbles. The end zones are now
  opaque, so the red one reads red.
