import { nextRandom } from './random.ts'
import { add, clampLength, distance, normalize, scale, sub, type Vec } from './vec.ts'

// Pitch units. x runs the length of the pitch, y its width. Team 0 attacks
// toward x = PITCH_LENGTH, team 1 toward x = 0.
export const PITCH_LENGTH = 60
export const PITCH_WIDTH = 30
export const END_ZONE_DEPTH = 5
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

export type Team = 0 | 1
export type Role = 'brawler' | 'runner' | 'centre'

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
}

export type Ball =
  | { kind: 'carried'; carrierId: number }
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
}

// Kickoff spots are written for a team attacking toward +x, and mirrored for
// team 1. The team with the ball lines up on ATTACK_FORMATION.
const ATTACK_FORMATION: [Role, Vec][] = [
  ['centre', { x: 29, y: 15 }],
  ['brawler', { x: 28, y: 11 }],
  ['brawler', { x: 28, y: 19 }],
  ['runner', { x: 24, y: 5 }],
  ['runner', { x: 24, y: 25 }],
]

// Kickoff spots for the team without the ball, in ATTACK_FORMATION's order.
const DEFENCE_FORMATION: Vec[] = [
  { x: 24, y: 15 },
  { x: 26, y: 11 },
  { x: 26, y: 19 },
  { x: 16, y: 8 },
  { x: 16, y: 22 },
]

export const attackDirection = (team: Team): number => (team === 0 ? 1 : -1)

export function createMatch(seed: number): Match {
  const match: Match = {
    seed,
    rngState: seed,
    clock: 0,
    score: [0, 0],
    players: [],
    ball: { kind: 'carried', carrierId: 0 },
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
    })
  }
  const centre = match.players.find((p) => p.team === receiving && p.role === 'centre')!
  match.ball = { kind: 'carried', carrierId: centre.id }
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
  resolveTackle(match)
  pickUpLooseBall(match)

  const holder = carrier(match)
  if (holder && holder.downFor === 0 && inScoringZone(holder)) {
    match.score[holder.team] += 1
    match.phase = { kind: 'scored', team: holder.team, resumeIn: SCORE_PAUSE_SECONDS }
  } else if (match.clock >= MATCH_SECONDS) {
    match.phase = { kind: 'ended' }
  }
}

function movePlayer(match: Match, p: Player) {
  if (p.downFor > 0) {
    p.downFor = Math.max(0, p.downFor - STEP_SECONDS)
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

function chooseTarget(match: Match, p: Player): { target: Vec; sprint: boolean } {
  const holder = carrier(match)
  const forward = attackDirection(p.team)
  if (!holder) {
    const ball = ballPosition(match)
    if (isLooseBallChaser(match, p, ball)) return { target: ball, sprint: true }
    // Hold a spot behind the ball in the player's own lane.
    const lane = toTeamFrame(p.team, p.formation).y
    return { target: keepOnPitch({ x: ball.x - forward * 5, y: lane }), sprint: false }
  }
  if (holder === p) return { target: carrierTarget(match, p), sprint: true }
  if (holder.team === p.team) {
    const ahead = p.role === 'runner' ? 8 : 3
    const lane = toTeamFrame(p.team, p.formation).y
    const target = keepOnPitch({ x: holder.pos.x + forward * ahead, y: (lane + holder.pos.y) / 2 })
    return { target, sprint: false }
  }
  // Chase the carrier, aiming where it will be once the chaser gets there.
  const lead = Math.min(1, distance(holder.pos, p.pos) / p.speed)
  return { target: add(holder.pos, scale(holder.vel, lead)), sprint: true }
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

function isLooseBallChaser(match: Match, p: Player, ball: Vec): boolean {
  const closer = match.players.filter(
    (o) => o.team === p.team && o.downFor === 0 && distance(o.pos, ball) < distance(p.pos, ball),
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
    (o) => o.team !== holder.team && o.downFor === 0 && distance(o.pos, holder.pos) < CONTACT_RANGE,
  )
  if (!tackler) return
  const tacklerWins = nextRandom(match) < tackler.strength / (tackler.strength + holder.strength)
  if (!tacklerWins) {
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

function pickUpLooseBall(match: Match) {
  const { ball } = match
  if (ball.kind !== 'loose' || ball.settleFor > 0) return
  let nearest: Player | undefined
  for (const p of match.players) {
    if (p.downFor > 0 || distance(p.pos, ball.pos) >= PICKUP_RANGE) continue
    if (!nearest || distance(p.pos, ball.pos) < distance(nearest.pos, ball.pos)) nearest = p
  }
  if (nearest) match.ball = { kind: 'carried', carrierId: nearest.id }
}
