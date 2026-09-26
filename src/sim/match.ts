import { nextRandom } from './random.ts'
import { add, clampLength, distance, length, normalize, scale, sub, type Vec } from './vec.ts'

// Pitch units. x runs the length of the pitch, y its width. Team 0 attacks
// toward x = PITCH_LENGTH, team 1 toward x = 0.
export const PITCH_LENGTH = 100
export const PITCH_WIDTH = 50
export const END_ZONE_DEPTH = 8
export const STEP_SECONDS = 1 / 20
export const MATCH_SECONDS = 180

const SCORE_PAUSE_SECONDS = 2
const CONTACT_RANGE = 1
const PICKUP_RANGE = 1
const PLAYER_SPACING = 0.9
const ACCELERATION = 20
const CARRIER_SPEED_FACTOR = 0.9
const TACKLED_DOWN_SECONDS = 2.5
const BROKEN_TACKLE_DOWN_SECONDS = 1.2
const FUMBLE_SPEED = 4
const FUMBLE_SETTLE_SECONDS = 0.4
const BALL_FRICTION_PER_STEP = 0.9
const LOOSE_BALL_CHASERS_PER_TEAM = 2
const CARRIER_THREAT_RANGE = 10
const FIGHT_SECONDS = 1
const FIGHT_DOWN_SECONDS = 3
const THROW_SPEED = 16
const CATCH_RANGE = 0.8
// Nobody can catch a throw until it has flown this far, so a defender
// pressed against the carrier cannot snatch it as it leaves the hand.
const CATCH_FREE_RELEASE = 2
// A carrier holds the ball this long before it may throw, so a catch is not
// thrown straight back out.
const MIN_HOLD_BEFORE_THROW = 1
// A throw risks a bad catch, so it must leave at least this many fewer
// units to cover than running on.
const PASS_GAIN_MIN = 5
const SAFETY_DEPTH = 15
const MARK_TACKLE_RANGE = 8
const SAFETY_ENGAGE_RANGE = 10

export type Team = 0 | 1
export type Role = 'brawler' | 'runner' | 'centre' | 'back'

export interface Player {
  id: number
  team: Team
  role: Role
  // Kickoff spot for a team attacking toward +x; mirrored for team 1.
  formation: Vec
  pos: Vec
  vel: Vec
  speed: number
  strength: number
  // Seconds left lying on the ground. Zero means standing.
  downFor: number
  // The opponent this player is locked in a fight with, if any.
  fight: { opponentId: number; endsIn: number } | undefined
}

export type Ball =
  | { kind: 'carried'; carrierId: number; heldFor: number }
  // A thrown ball flies straight at a fixed speed and lands loose at landAt
  // unless a player catches it on the way.
  | { kind: 'flying'; pos: Vec; from: Vec; landAt: Vec; throwerId: number }
  // settleFor: seconds before anyone can grab it, so a fumble scatters
  // before the tackler standing over it can pick it straight back up.
  | { kind: 'loose'; pos: Vec; vel: Vec; settleFor: number }

export type Phase =
  | { kind: 'play' }
  | { kind: 'scored'; team: Team; resumeIn: number }
  | { kind: 'ended' }

export interface Match {
  seed: number
  rngState: number
  // Seconds of play elapsed. The clock stops while a score is celebrated.
  clock: number
  score: [number, number]
  players: Player[]
  ball: Ball
  phase: Phase
}

interface RoleProfile {
  speed: number
  strength: number
}

const ROLE_PROFILES: Record<Role, RoleProfile> = {
  brawler: { speed: 5.5, strength: 8 },
  runner: { speed: 7, strength: 4 },
  centre: { speed: 6.5, strength: 6 },
  back: { speed: 6.5, strength: 5 },
}

// Kickoff spots are written for a team attacking toward +x, and mirrored for
// team 1. The team with the ball lines up on ATTACK_FORMATION.
const ATTACK_FORMATION: [Role, Vec][] = [
  ['centre', { x: 49, y: 25 }],
  ['brawler', { x: 47, y: 15 }],
  ['brawler', { x: 47, y: 20 }],
  ['brawler', { x: 47, y: 30 }],
  ['brawler', { x: 47, y: 35 }],
  ['brawler', { x: 45, y: 25 }],
  ['runner', { x: 42, y: 6 }],
  ['runner', { x: 42, y: 44 }],
  ['runner', { x: 38, y: 25 }],
  ['back', { x: 32, y: 15 }],
  ['back', { x: 32, y: 35 }],
]

// Kickoff spots for the team without the ball, in ATTACK_FORMATION's order.
const DEFENCE_FORMATION: Vec[] = [
  { x: 40, y: 25 },
  { x: 45, y: 15 },
  { x: 45, y: 20 },
  { x: 45, y: 30 },
  { x: 45, y: 35 },
  { x: 43, y: 25 },
  { x: 35, y: 8 },
  { x: 35, y: 42 },
  { x: 33, y: 25 },
  { x: 22, y: 15 },
  { x: 22, y: 35 },
]

export const attackDirection = (team: Team): number => (team === 0 ? 1 : -1)

export function createMatch(seed: number): Match {
  const match: Match = {
    seed,
    rngState: seed,
    clock: 0,
    score: [0, 0],
    players: [],
    ball: { kind: 'carried', carrierId: 0, heldFor: 0 },
    phase: { kind: 'play' },
  }
  for (const team of [0, 1] as const) {
    ATTACK_FORMATION.forEach(([role, formation]) => {
      const profile = ROLE_PROFILES[role]
      match.players.push({
        id: match.players.length,
        team,
        role,
        formation,
        pos: { x: 0, y: 0 },
        vel: { x: 0, y: 0 },
        speed: profile.speed * (0.9 + 0.2 * nextRandom(match)),
        strength: profile.strength * (0.9 + 0.2 * nextRandom(match)),
        downFor: 0,
        fight: undefined,
      })
    })
  }
  kickOff(match, 0)
  return match
}

function toTeamFrame(team: Team, spot: Vec): Vec {
  return team === 0 ? spot : { x: PITCH_LENGTH - spot.x, y: spot.y }
}

function kickOff(match: Match, receiving: Team) {
  for (const team of [0, 1] as const) {
    const players = match.players.filter((p) => p.team === team)
    players.forEach((p, i) => {
      p.pos = toTeamFrame(team, team === receiving ? p.formation : DEFENCE_FORMATION[i])
      p.vel = { x: 0, y: 0 }
      p.downFor = 0
      p.fight = undefined
    })
  }
  const centre = match.players.find((p) => p.team === receiving && p.role === 'centre')!
  match.ball = { kind: 'carried', carrierId: centre.id, heldFor: 0 }
}

export function carrier(match: Match): Player | undefined {
  const { ball } = match
  return ball.kind === 'carried' ? match.players[ball.carrierId] : undefined
}

export function ballPosition(match: Match): Vec {
  const { ball } = match
  return ball.kind === 'carried' ? match.players[ball.carrierId].pos : ball.pos
}

function inScoringZone(player: Player): boolean {
  return player.team === 0
    ? player.pos.x >= PITCH_LENGTH - END_ZONE_DEPTH
    : player.pos.x <= END_ZONE_DEPTH
}

export function step(match: Match) {
  const { phase } = match
  if (phase.kind === 'ended') return
  if (phase.kind === 'scored') {
    phase.resumeIn -= STEP_SECONDS
    if (phase.resumeIn <= 0) {
      kickOff(match, phase.team === 0 ? 1 : 0)
      match.phase = { kind: 'play' }
    }
    return
  }

  match.clock += STEP_SECONDS
  for (const p of match.players) movePlayer(match, p)
  separatePlayers(match)
  moveBall(match)
  resolveFights(match)
  startFights(match)
  resolveTackle(match)
  pickUpLooseBall(match)
  catchFlyingBall(match)
  throwIfBetterPlaced(match)

  const holder = carrier(match)
  if (holder && holder.downFor === 0 && inScoringZone(holder)) {
    match.score[holder.team] += 1
    match.phase = { kind: 'scored', team: holder.team, resumeIn: SCORE_PAUSE_SECONDS }
  } else if (match.clock >= MATCH_SECONDS) {
    match.phase = { kind: 'ended' }
  }
}

// A player who can run, tackle, catch and pick up the ball.
const isFree = (p: Player) => p.downFor === 0 && !p.fight

function movePlayer(match: Match, p: Player) {
  if (p.downFor > 0) {
    p.downFor = Math.max(0, p.downFor - STEP_SECONDS)
    p.vel = { x: 0, y: 0 }
    return
  }
  if (p.fight) {
    p.vel = { x: 0, y: 0 }
    return
  }
  const { target, sprint } = chooseTarget(match, p)
  const holder = carrier(match)
  const topSpeed = holder === p ? p.speed * CARRIER_SPEED_FACTOR : p.speed
  // A player taking up a spot slows on arrival instead of circling it. A
  // player going for the ball or the carrier never slows, or it would trail
  // a carrier of equal speed without ever making contact.
  const speed = sprint ? topSpeed : Math.min(topSpeed, distance(target, p.pos) * 2)
  const wanted = scale(normalize(sub(target, p.pos)), speed)
  p.vel = add(p.vel, clampLength(sub(wanted, p.vel), ACCELERATION * STEP_SECONDS))
  p.pos = keepOnPitch(add(p.pos, scale(p.vel, STEP_SECONDS)))
}

function keepOnPitch(pos: Vec): Vec {
  return {
    x: Math.min(PITCH_LENGTH, Math.max(0, pos.x)),
    y: Math.min(PITCH_WIDTH, Math.max(0, pos.y)),
  }
}

// The role table: what each role does in each state of the ball.
function chooseTarget(match: Match, p: Player): { target: Vec; sprint: boolean } {
  const { ball } = match
  if (ball.kind !== 'carried') {
    const spot = ball.kind === 'flying' ? ball.landAt : ball.pos
    if (isBallChaser(match, p, spot)) return { target: spot, sprint: true }
    return { target: holdBehind(p, spot), sprint: false }
  }
  const holder = match.players[ball.carrierId]
  if (holder === p) return { target: carrierTarget(match, p), sprint: true }
  if (holder.team === p.team) {
    if (p.role === 'brawler') return blockFor(match, p, holder)
    if (p.role === 'runner') return { target: openSpace(match, p, holder), sprint: false }
    return { target: holdBehind(p, holder.pos), sprint: false }
  }
  if (p.role === 'back') {
    const safetySpot = safetyTarget(p, holder)
    if (safetySpot) return { target: safetySpot, sprint: false }
  }
  if (p.role === 'runner' && distance(p.pos, holder.pos) > MARK_TACKLE_RANGE) {
    const mark = markTarget(match, p)
    if (mark) return { target: mark, sprint: true }
  }
  // Brawlers and the centre go for the carrier. The opposing line blocks the
  // way, so a brawler's run at the carrier becomes a push through the line.
  return { target: interceptCarrier(p, holder), sprint: true }
}

// Chase the carrier, aiming where it will be once the chaser gets there.
function interceptCarrier(p: Player, holder: Player): Vec {
  const lead = Math.min(1, distance(holder.pos, p.pos) / p.speed)
  return add(holder.pos, scale(holder.vel, lead))
}

// A spot behind the ball in the player's own lane.
function holdBehind(p: Player, ball: Vec): Vec {
  const lane = toTeamFrame(p.team, p.formation).y
  return keepOnPitch({ x: ball.x - attackDirection(p.team) * 5, y: lane })
}

// Run at the nearest free opponent ahead of the carrier, to fight it out of
// the carrier's way. With nobody ahead, lead the carrier upfield.
function blockFor(match: Match, p: Player, holder: Player): { target: Vec; sprint: boolean } {
  const forward = attackDirection(p.team)
  const inPath = match.players.filter(
    (o) =>
      o.team !== p.team &&
      isFree(o) &&
      (o.pos.x - holder.pos.x) * forward > -1 &&
      distance(o.pos, holder.pos) < CARRIER_THREAT_RANGE,
  )
  const opponent = nearest(p.pos, inPath)
  if (opponent) return { target: opponent.pos, sprint: true }
  const lane = toTeamFrame(p.team, p.formation).y
  return { target: keepOnPitch({ x: holder.pos.x + forward * 3, y: (lane + holder.pos.y) / 2 }), sprint: false }
}

// Of a few spots upfield of the carrier, take the one least threatened.
function openSpace(match: Match, p: Player, holder: Player): Vec {
  const forward = attackDirection(p.team)
  const lane = toTeamFrame(p.team, p.formation).y
  let best: Vec | undefined
  let bestThreat = Infinity
  for (const dy of [-8, 0, 8]) {
    const spot = keepOnPitch({ x: holder.pos.x + forward * 12, y: lane + dy })
    const threat = threatAt(match, p.team, spot)
    if (threat < bestThreat) {
      best = spot
      bestThreat = threat
    }
  }
  return best!
}

// Stay deep between the carrier and the own end zone, until the carrier
// comes close enough to tackle. Returns undefined when it is time to tackle.
function safetyTarget(p: Player, holder: Player): Vec | undefined {
  if (distance(p.pos, holder.pos) < SAFETY_ENGAGE_RANGE) return undefined
  const ownGoalLine = p.team === 0 ? END_ZONE_DEPTH : PITCH_LENGTH - END_ZONE_DEPTH
  const forward = attackDirection(p.team)
  const deepest = ownGoalLine + forward * SAFETY_DEPTH
  // Never stand upfield of the carrier: a safety behind the play is no use.
  const x = forward > 0 ? Math.min(deepest, holder.pos.x - 2) : Math.max(deepest, holder.pos.x + 2)
  const lane = toTeamFrame(p.team, p.formation).y
  return keepOnPitch({ x, y: (lane + holder.pos.y) / 2 })
}

// Stand goal-side of the nearest opposing runner, to cut out a pass to it.
function markTarget(match: Match, p: Player): Vec | undefined {
  const receiver = nearest(
    p.pos,
    match.players.filter((o) => o.team !== p.team && o.role === 'runner' && o.downFor === 0),
  )
  if (!receiver) return undefined
  return keepOnPitch({ x: receiver.pos.x - attackDirection(p.team) * 2, y: receiver.pos.y })
}

function nearest(from: Vec, players: Player[]): Player | undefined {
  let best: Player | undefined
  for (const o of players) {
    if (!best || distance(o.pos, from) < distance(best.pos, from)) best = o
  }
  return best
}

// The carrier always drives forward and sidesteps the opponents ahead of it.
// Dodging straight away from them would turn it back toward its own end zone.
function carrierTarget(match: Match, p: Player): Vec {
  const forward = attackDirection(p.team)
  const heading: Vec = { x: forward, y: 0 }
  for (const other of match.players) {
    if (other.team === p.team || other.downFor > 0) continue
    if ((other.pos.x - p.pos.x) * forward < 0) continue
    const d = distance(other.pos, p.pos)
    if (d >= CARRIER_THREAT_RANGE) continue
    // Break a dead-level tie toward the middle of the pitch.
    const side = Math.sign(p.pos.y - other.pos.y) || Math.sign(PITCH_WIDTH / 2 - p.pos.y) || 1
    heading.y += (side * 1.5 * (CARRIER_THREAT_RANGE - d)) / CARRIER_THREAT_RANGE
  }
  // Keep the carrier off the side lines, where it would be pinned.
  if (p.pos.y < 3) heading.y += 1
  if (p.pos.y > PITCH_WIDTH - 3) heading.y -= 1
  return add(p.pos, scale(normalize(heading), 5))
}

function isBallChaser(match: Match, p: Player, ball: Vec): boolean {
  const closer = match.players.filter(
    (o) => o.team === p.team && isFree(o) && distance(o.pos, ball) < distance(p.pos, ball),
  )
  return closer.length < LOOSE_BALL_CHASERS_PER_TEAM
}

function separatePlayers(match: Match) {
  const standing = match.players.filter((p) => p.downFor === 0)
  for (let i = 0; i < standing.length; i++) {
    for (let j = i + 1; j < standing.length; j++) {
      const a = standing[i]
      const b = standing[j]
      const d = distance(a.pos, b.pos)
      if (d >= PLAYER_SPACING || d === 0) continue
      const push = scale(normalize(sub(b.pos, a.pos)), (PLAYER_SPACING - d) / 2)
      a.pos = keepOnPitch(sub(a.pos, push))
      b.pos = keepOnPitch(add(b.pos, push))
    }
  }
}

function moveBall(match: Match) {
  const { ball } = match
  if (ball.kind === 'carried') ball.heldFor += STEP_SECONDS
  if (ball.kind === 'flying') {
    const toGo = sub(ball.landAt, ball.pos)
    const stride = THROW_SPEED * STEP_SECONDS
    if (length(toGo) <= stride) {
      match.ball = { kind: 'loose', pos: ball.landAt, vel: { x: 0, y: 0 }, settleFor: 0 }
    } else {
      ball.pos = add(ball.pos, scale(normalize(toGo), stride))
    }
    return
  }
  if (ball.kind !== 'loose') return
  ball.settleFor = Math.max(0, ball.settleFor - STEP_SECONDS)
  ball.pos = add(ball.pos, scale(ball.vel, STEP_SECONDS))
  ball.vel = scale(ball.vel, BALL_FRICTION_PER_STEP)
  if (ball.pos.y < 0 || ball.pos.y > PITCH_WIDTH) ball.vel.y = -ball.vel.y
  if (ball.pos.x < 0 || ball.pos.x > PITCH_LENGTH) ball.vel.x = -ball.vel.x
  ball.pos = keepOnPitch(ball.pos)
}

function resolveTackle(match: Match) {
  const holder = carrier(match)
  if (!holder) return
  const tackler = match.players.find(
    (o) => o.team !== holder.team && isFree(o) && distance(o.pos, holder.pos) < CONTACT_RANGE,
  )
  if (!tackler) return
  if (!winsContest(match, tackler, holder)) {
    tackler.downFor = BROKEN_TACKLE_DOWN_SECONDS
    return
  }
  holder.downFor = TACKLED_DOWN_SECONDS
  holder.vel = { x: 0, y: 0 }
  const angle = nextRandom(match) * 2 * Math.PI
  match.ball = {
    kind: 'loose',
    pos: { ...holder.pos },
    vel: { x: Math.cos(angle) * FUMBLE_SPEED, y: Math.sin(angle) * FUMBLE_SPEED },
    settleFor: FUMBLE_SETTLE_SECONDS,
  }
}

// A strength contest weighted by chance. True if a beats b.
function winsContest(match: Match, a: Player, b: Player): boolean {
  return nextRandom(match) < a.strength / (a.strength + b.strength)
}

function pickUpLooseBall(match: Match) {
  const { ball } = match
  if (ball.kind !== 'loose' || ball.settleFor > 0) return
  const taker = nearest(
    ball.pos,
    match.players.filter((p) => isFree(p) && distance(p.pos, ball.pos) < PICKUP_RANGE),
  )
  if (taker) match.ball = { kind: 'carried', carrierId: taker.id, heldFor: 0 }
}

function catchFlyingBall(match: Match) {
  const { ball } = match
  if (ball.kind !== 'flying') return
  const catcher = nearest(
    ball.pos,
    match.players.filter((p) => p.id !== ball.throwerId && isFree(p) && distance(p.pos, ball.pos) < CATCH_RANGE),
  )
  if (distance(ball.pos, ball.from) < CATCH_FREE_RELEASE) return
  if (catcher) match.ball = { kind: 'carried', carrierId: catcher.id, heldFor: 0 }
}

// A brawler who reaches an opponent without the ball locks it in a fight.
function startFights(match: Match) {
  const holder = carrier(match)
  for (const p of match.players) {
    if (p.role !== 'brawler' || p === holder || !isFree(p)) continue
    const opponent = match.players.find(
      (o) => o.team !== p.team && o !== holder && isFree(o) && distance(o.pos, p.pos) < CONTACT_RANGE,
    )
    if (!opponent) continue
    p.fight = { opponentId: opponent.id, endsIn: FIGHT_SECONDS }
    opponent.fight = { opponentId: p.id, endsIn: FIGHT_SECONDS }
  }
}

function resolveFights(match: Match) {
  for (const p of match.players) {
    if (!p.fight || p.id > p.fight.opponentId) continue
    const opponent = match.players[p.fight.opponentId]
    p.fight.endsIn -= STEP_SECONDS
    if (p.fight.endsIn > 0) continue
    const loser = winsContest(match, p, opponent) ? opponent : p
    loser.downFor = FIGHT_DOWN_SECONDS
    p.fight = undefined
    opponent.fight = undefined
  }
}

// How badly the opponents of `team` endanger a player standing at `at`. The
// worst single opponent counts: near is worse than far, and an opponent
// upfield is up to five times worse than one behind.
function threatAt(match: Match, team: Team, at: Vec): number {
  const forward = attackDirection(team)
  let worst = 0
  for (const o of match.players) {
    if (o.team === team || !isFree(o)) continue
    const diff = sub(o.pos, at)
    const d2 = Math.max(diff.x * diff.x + diff.y * diff.y, 0.25)
    const ahead = (normalize(diff).x * forward + 1) / 2
    worst = Math.max(worst, (4 * ahead + 1) / d2)
  }
  return worst
}

// Units a player still has to cover after running straight for the line
// from `from` until the first free opponent can reach it. Zero means a clear
// run to score. Opponents get `headStart` seconds to close in first, which is
// the flight time when the player is waiting on a throw.
function groundLeft(match: Match, team: Team, from: Vec, speed: number, headStart: number): number {
  const toLine = team === 0 ? PITCH_LENGTH - END_ZONE_DEPTH - from.x : from.x - END_ZONE_DEPTH
  if (toLine <= 0) return 0
  const run: Vec = { x: attackDirection(team) * speed, y: 0 }
  let contact = Infinity
  for (const o of match.players) {
    if (o.team === team || !isFree(o)) continue
    contact = Math.min(contact, catchUpTime(sub(from, o.pos), run, o.speed, headStart))
  }
  return Math.max(0, toLine - speed * contact)
}

// Earliest t >= 0 at which a chaser of speed `chaserSpeed`, starting at the
// origin with `headStart` seconds of running, can reach a runner at `offset`
// moving with velocity `run`: the least t with
// |offset + run·t| <= chaserSpeed·(t + headStart). Infinity if never.
function catchUpTime(offset: Vec, run: Vec, chaserSpeed: number, headStart: number): number {
  const f = (t: number) =>
    (offset.x + run.x * t) ** 2 + (offset.y + run.y * t) ** 2 - (chaserSpeed * (t + headStart)) ** 2
  if (f(0) <= 0) return 0
  const s2 = chaserSpeed * chaserSpeed
  const a = run.x * run.x + run.y * run.y - s2
  const b = 2 * (offset.x * run.x + offset.y * run.y - s2 * headStart)
  const c = f(0)
  if (Math.abs(a) < 1e-9) return b < 0 ? -c / b : Infinity
  const disc = b * b - 4 * a * c
  if (disc < 0) return Infinity
  const roots = [(-b - Math.sqrt(disc)) / (2 * a), (-b + Math.sqrt(disc)) / (2 * a)].sort((m, n) => m - n)
  // f(0) > 0 here. A faster chaser (a < 0) always closes in, at the larger
  // root. A slower one (a > 0) is close enough only between the roots.
  if (a < 0) return roots[1]
  return roots[0] >= 0 ? roots[0] : Infinity
}

// True if a free opponent can reach the ball's path before the ball passes.
function laneIsCovered(match: Match, team: Team, from: Vec, to: Vec): boolean {
  const length = distance(from, to)
  const along = normalize(sub(to, from))
  for (let d = CATCH_FREE_RELEASE; d <= length; d += 1) {
    const point = add(from, scale(along, d))
    const arrives = d / THROW_SPEED
    for (const o of match.players) {
      if (o.team === team || !isFree(o)) continue
      if (distance(o.pos, point) - CATCH_RANGE <= o.speed * arrives) return true
    }
  }
  return false
}

// The carrier throws when a free runner or back, at the spot the throw would
// land, is left much less ground to cover than the carrier running on, and
// no opponent can cut out the throw. The throw leads the receiver.
function throwIfBetterPlaced(match: Match) {
  const { ball } = match
  if (ball.kind !== 'carried' || ball.heldFor < MIN_HOLD_BEFORE_THROW) return
  const holder = match.players[ball.carrierId]
  if (!isFree(holder)) return
  const runSpeed = (p: Player) => p.speed * CARRIER_SPEED_FACTOR
  const ownLeft = groundLeft(match, holder.team, holder.pos, runSpeed(holder), 0)
  if (ownLeft === 0) return
  let best: { landAt: Vec; left: number } | undefined
  for (const p of match.players) {
    if (p.team !== holder.team || p === holder || !isFree(p)) continue
    if (p.role !== 'runner' && p.role !== 'back') continue
    const flightSeconds = distance(holder.pos, p.pos) / THROW_SPEED
    const landAt = keepOnPitch(add(p.pos, scale(p.vel, flightSeconds)))
    const left = groundLeft(match, p.team, landAt, runSpeed(p), flightSeconds)
    if (left + PASS_GAIN_MIN > ownLeft || (best && left >= best.left)) continue
    if (laneIsCovered(match, holder.team, holder.pos, landAt)) continue
    best = { landAt, left }
  }
  if (!best) return
  match.ball = { kind: 'flying', pos: { ...holder.pos }, from: { ...holder.pos }, landAt: best.landAt, throwerId: holder.id }
}
