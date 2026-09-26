# Harpastum

A sports management sim set in the Roman world, built on the ancient ball
game harpastum, for Matt to design and play on his phone. The player coaches a
team, sets tactics and formations, and watches a match simulation play them
out. The game is contact football with almost no rules: each team tries to
carry the ball into the opponent's end zone, and any player may tackle, block
or fight any opponent at any time. The match simulation is the core of the
game, and its design is still open.

## Glossary

**Match** — one game between two teams of five, from kickoff to full time,
fully set by its seed. *Currently:* `Match`, `createMatch` and `step` in
`src/sim/match.ts`.

**Seed** — the number that sets every random choice in a match, so the same
seed replays the same match. *Currently:* `Match.seed`, drawn through
`nextRandom` in `src/sim/random.ts`; shown under the score.

**Step** — the fixed slice of match time by which the simulation advances.
*Currently:* `step` and `STEP_SECONDS` (1/20 s) in `src/sim/match.ts`.

**Kickoff** — the start of play: the ball at the centre, each team in its own
half. After a score, the team that conceded kicks off. *Currently:* `kickOff`,
`ATTACK_FORMATION` and `DEFENCE_FORMATION` in `src/sim/match.ts`.

**End zone** — the area at each end of the pitch. A carrier who stands in the
opponent's end zone scores. *Currently:* `END_ZONE_DEPTH` and
`inScoringZone` in `src/sim/match.ts`.

**Carrier** — the player who holds the ball. *Currently:* `carrier()` and the
`carried` ball in `src/sim/match.ts`.

**Loose ball** — a ball that no player holds. The nearest players of each
team chase it. *Currently:* the `loose` ball and `isLooseBallChaser` in
`src/sim/match.ts`.

**Tackle** — a strength contest, weighted by chance, when a player reaches the
opposing carrier. The loser is knocked down. Play does not stop: there are no
downs. *Currently:* `resolveTackle` in `src/sim/match.ts`.

**Fumble** — the ball coming loose from a tackled carrier. It scatters, and
nobody can pick it up for a moment. *Currently:* `resolveTackle` and
`settleFor` in `src/sim/match.ts`.

**Knock-down** — a player lying on the ground for a few seconds, unable to
act. *Currently:* `Player.downFor` in `src/sim/match.ts`.

**Fight** — a short locked bout between two opposing players away from the
ball, which ends with the loser knocked down. *Currently:* `startFights`,
`resolveFights` and `Player.fight` in `src/sim/match.ts`.

**Pass** — a throw by the carrier in any direction, which a player of either
team may catch. *Currently:* `throwIfThreatened`, `catchFlyingBall` and the
`flying` ball in `src/sim/match.ts`.

**Role** — a player's job on the team: brawler (fights and blocks), runner
(pass target, and deep safety on defence) or centre (starts with the ball;
linebacker on defence). *Currently:* `Role` and `ROLE_PROFILES` in
`src/sim/match.ts`.

**Role table** — for each role, the behaviour to follow in each state of the
ball: loose, in the air, carried by own team, carried by the opponent.
*Currently:* `chooseTarget` in `src/sim/match.ts`.

**Threat score** — how badly opponents endanger a player, used by the carrier
to decide whether to pass. *Currently:* `threatAt` in `src/sim/match.ts`,
adapted from `legacy/Threat.py`.

**Legacy match AI** — the 2013 Python attempt at the match simulation, kept
unchanged as a design reference. It does not run. *Currently:* `legacy/`.

## Decisions

None.

## Facts

None.
