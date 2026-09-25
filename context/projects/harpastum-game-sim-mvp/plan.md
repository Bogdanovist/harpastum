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
watches a 5-a-side match play itself out: players run, pass, tackle and
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

- The pitch is 60 × 30 units with a 5-unit end zone at each end. 100 × 50
  was sized for 11-a-side, and 5 players on it would rarely meet.
- The match starts with the ball at the centre and both teams in their own
  half. After a score, the teams reset and the team that conceded gets the
  ball at the centre.
- A match lasts 3 minutes of real time at normal speed. The score and clock
  show at the top of the screen.

### Players and roles (5 a side)

Each player has a speed and a strength. A player who is knocked down lies
prone for a few seconds, then stands up.

| Role | Count | Own team has the ball | Opponent has the ball |
|---|---|---|---|
| Brawler | 2 | Runs ahead of the carrier and fights the nearest opponent in its path | Fights the opposing brawlers, then goes for the carrier |
| Runner | 2 | Finds open space toward the end zone as a pass target | Safety: stays deep and tackles a carrier who breaks through |
| Centre | 1 | Starts with the ball; runs, and passes when a runner is less threatened | Linebacker: goes straight for the carrier |

When the ball is loose, the nearest two players on each team chase it. When
it is in the air, the nearest players run to where it will land.

### Contact

- **Tackle.** A player who reaches the carrier makes a strength contest,
  weighted by random chance. The winner stays up. If the tackler wins, the
  carrier goes down and the ball comes loose where it fell. There are no
  downs: play never stops except after a score.
- **Fight.** A player who reaches any opponent without the ball can engage
  it. Both stay locked in place for a short bout, then a strength contest
  knocks the loser down. A player in a fight cannot tackle or catch.
- **Pass.** The carrier may throw in any direction. The ball flies in a
  straight line along the ground plane at a fixed speed. Any player, either
  team, within reach of it as it passes may catch it. A throw nobody catches
  lands loose.

### Screen

The match draws to a `<canvas>` at a low resolution (the pitch at 4 pixels
per unit is 240 × 120), scaled up to the phone width with smoothing off, so
it reads as 8-bit. On a phone in portrait the pitch runs top to bottom.
Players are 8 × 8 sprites drawn in code, in two team colours, with a
different shape per role and a flat, lying pose when knocked down. There are
no image files.

The title screen's button opens the match. The match screen has three
controls: pause, speed (1×, 2×, 4×) and new match (a new seed). The seed
shows under the score.

### Slices

Each slice is one PR in a worktree, shown on the phone before it merges.

1. **Players run and score.** Sim core, seeded random numbers, pitch, the
   match screen with pixel sprites. The centre carries the ball; defenders
   chase and tackle; the ball comes loose; the ball is re-taken; scores and
   resets happen; the clock ends the match. A Vitest test runs a seeded
   match to the end.
2. **Roles, fights and passes.** The role table, fights, knock-downs,
   throwing and catching. After this slice the match looks like harpastum.

## Decisions (Matt, 2026-09-25)

1. **Seeded, fixed-step sim separate from the screen.** Matches replay from
   a seed and are testable. Every random choice must go through the sim's
   generator.
2. **Pitch 60 × 30 with 5-unit end zones, drawn top to bottom in portrait.**
3. **A tackle knocks the carrier down and the ball comes loose. No downs.**
   The alternative, a tackle that stops play for a restart like American
   football, gives a set-play game and more to design later.
4. **Passes in any direction, catchable by either team.**
5. **Fights as short locked bouts with a knock-down.** Knock-downs last
   seconds. There are no injuries and no send-offs.
6. **The five roles and their behaviours as in the table.**
7. **A 3-minute match, watch-only, with pause, speed and new match.**
8. **Two slices,** fights and passing in the second.

## Out of scope

- 11-a-side, team selection, tactics, formations and player attributes set
  by the player.
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
  tune the match in a later session. Slice 2 (roles, fights and passes) has
  not started.
