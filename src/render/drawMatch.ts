import {
  END_ZONE_DEPTH,
  PITCH_LENGTH,
  PITCH_WIDTH,
  type Match,
  type Player,
  type Role,
  type Team,
} from '../sim/match.ts'
import { add, distance, type Vec } from '../sim/vec.ts'

// The canvas is drawn at this low resolution and scaled up with smoothing
// off, which gives the 8-bit look. The pitch runs top to bottom so it fills a
// phone held in portrait. Team 0 attacks toward the top.
const PIXELS_PER_UNIT = 4
const MARGIN = 6
export const CANVAS_WIDTH = PITCH_WIDTH * PIXELS_PER_UNIT + MARGIN * 2
export const CANVAS_HEIGHT = PITCH_LENGTH * PIXELS_PER_UNIT + MARGIN * 2

// zone: the end-zone fill. It is opaque, because a translucent red over the
// green grass reads as olive.
const TEAM_COLOURS: Record<Team, { main: string; dark: string; zone: string }> = {
  0: { main: '#c8402e', dark: '#7a2319', zone: '#8c3a2c' },
  1: { main: '#3a68c8', dark: '#213e7a', zone: '#34508a' },
}

const PALETTE: Record<string, string> = {
  k: '#1a1410',
  s: '#e0a878',
  h: '#e8c040',
}

// 8 × 8 sprites, one per role. t and d take the team's main and dark
// colours; '.' is transparent.
const SPRITES: Record<Role, string[]> = {
  brawler: [
    '..ssss..',
    '..ssss..',
    'tttttttt',
    'tttddttt',
    'tttttttt',
    '.tt..tt.',
    '.ss..ss.',
    '.kk..kk.',
  ],
  runner: [
    '...ss...',
    '...ss...',
    '..tttt..',
    '.s.tt.s.',
    '...dd...',
    '..t..t..',
    '..s..s..',
    '..k..k..',
  ],
  back: [
    '...ss...',
    '...ss...',
    '.tdddt..',
    's.tttt.s',
    '..tddt..',
    '..t..t..',
    '..s..s..',
    '..k..k..',
  ],
  centre: [
    '..hhhh..',
    '..ssss..',
    '.tttttt.',
    's.tddt.s',
    '..tttt..',
    '..t..t..',
    '..s..s..',
    '..k..k..',
  ],
}

function toScreen(pos: Vec): Vec {
  return {
    x: Math.round(MARGIN + pos.y * PIXELS_PER_UNIT),
    y: Math.round(MARGIN + (PITCH_LENGTH - pos.x) * PIXELS_PER_UNIT),
  }
}

export function drawMatch(ctx: CanvasRenderingContext2D, match: Match) {
  drawPitch(ctx)
  const byDepth = [...match.players].sort((a, b) => toScreen(a.pos).y - toScreen(b.pos).y)
  // Fighters shake from side to side, in turn, four times a second.
  const shake = Math.floor(match.clock * 8) % 2 === 0 ? 1 : -1
  for (const p of byDepth) drawPlayer(ctx, p, p.fight ? shake * (p.team === 0 ? 1 : -1) : 0)
  drawBall(ctx, match)
}

function drawPitch(ctx: CanvasRenderingContext2D) {
  ctx.fillStyle = '#1c1712'
  ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)
  const bandUnits = 5
  for (let x = 0; x < PITCH_LENGTH; x += bandUnits) {
    const top = toScreen({ x: x + bandUnits, y: 0 })
    ctx.fillStyle = (x / bandUnits) % 2 === 0 ? '#3f7a2c' : '#4a8a33'
    ctx.fillRect(top.x, top.y, PITCH_WIDTH * PIXELS_PER_UNIT, bandUnits * PIXELS_PER_UNIT)
  }
  // Each end zone is tinted with the colour of the team that defends it.
  const depth = END_ZONE_DEPTH * PIXELS_PER_UNIT
  const width = PITCH_WIDTH * PIXELS_PER_UNIT
  ctx.fillStyle = TEAM_COLOURS[1].zone
  ctx.fillRect(MARGIN, MARGIN, width, depth)
  ctx.fillStyle = TEAM_COLOURS[0].zone
  ctx.fillRect(MARGIN, CANVAS_HEIGHT - MARGIN - depth, width, depth)

  ctx.fillStyle = '#e8e0c8'
  for (const x of [END_ZONE_DEPTH, PITCH_LENGTH / 2, PITCH_LENGTH - END_ZONE_DEPTH]) {
    ctx.fillRect(MARGIN, toScreen({ x, y: 0 }).y, width, 1)
  }
  ctx.strokeStyle = '#e8e0c8'
  ctx.lineWidth = 1
  ctx.strokeRect(MARGIN - 0.5, MARGIN - 0.5, width + 1, PITCH_LENGTH * PIXELS_PER_UNIT + 1)
}

function drawPlayer(ctx: CanvasRenderingContext2D, p: Player, shiftX: number) {
  const sprite = SPRITES[p.role]
  const colours: Record<string, string> = {
    ...PALETTE,
    t: TEAM_COLOURS[p.team].main,
    d: TEAM_COLOURS[p.team].dark,
  }
  const feet = add(toScreen(p.pos), { x: shiftX, y: 0 })
  const down = p.downFor > 0
  for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 8; col++) {
      const colour = colours[sprite[row][col]]
      if (!colour) continue
      ctx.fillStyle = colour
      // A player on the ground is the standing sprite turned on its side and
      // squashed to half height.
      if (down) ctx.fillRect(feet.x - 4 + row, feet.y - 4 + Math.floor((7 - col) / 2), 1, 1)
      else ctx.fillRect(feet.x - 4 + col, feet.y - 7 + row, 1, 1)
    }
  }
}

function drawBall(ctx: CanvasRenderingContext2D, match: Match) {
  const { ball } = match
  let at: Vec
  if (ball.kind === 'carried') {
    at = add(toScreen(match.players[ball.carrierId].pos), { x: 3, y: -4 })
  } else if (ball.kind === 'flying') {
    // A ball in the air rises and falls on an arc above its shadow, higher
    // for a longer throw, and is drawn larger so a pass reads at a glance.
    const total = distance(ball.from, ball.landAt)
    const progress = total === 0 ? 1 : distance(ball.from, ball.pos) / total
    const height = Math.round(Math.sin(progress * Math.PI) * (4 + total * 0.8))
    const ground = toScreen(ball.pos)
    ctx.fillStyle = 'rgba(0, 0, 0, 0.45)'
    ctx.fillRect(ground.x - 2, ground.y, 5, 2)
    drawBallAt(ctx, add(ground, { x: 0, y: -4 - height }), 2)
    return
  } else {
    at = toScreen(ball.pos)
  }
  drawBallAt(ctx, at, 1)
}

// A ball of radius r pixels, with a dark outline that keeps it visible
// against the grass and the players.
function drawBallAt(ctx: CanvasRenderingContext2D, at: Vec, r: number) {
  const d = 2 * r + 1
  ctx.fillStyle = PALETTE.k
  ctx.fillRect(at.x - r - 1, at.y - r, d + 2, d)
  ctx.fillRect(at.x - r, at.y - r - 1, d, d + 2)
  ctx.fillStyle = '#e8b870'
  ctx.fillRect(at.x - r, at.y - r, d, d)
  ctx.fillStyle = '#fff0c8'
  ctx.fillRect(at.x - r, at.y - r, r, r)
}
