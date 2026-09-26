import { describe, expect, test } from 'vitest'
import { carrier, createMatch, MATCH_SECONDS, step, STEP_SECONDS, type Match } from './match.ts'

function playToEnd(match: Match): Match {
  while (match.phase.kind !== 'ended') step(match)
  return match
}

describe('a match', () => {
  test('replays identically from the same seed', () => {
    expect(playToEnd(createMatch(42))).toEqual(playToEnd(createMatch(42)))
  })

  test('ends when the clock reaches full time', () => {
    const match = playToEnd(createMatch(7))
    expect(match.clock).toBeGreaterThanOrEqual(MATCH_SECONDS)
    expect(match.clock).toBeLessThan(MATCH_SECONDS + 0.1)
  })

  test('produces scores for both teams across a run of seeds', () => {
    const totals = [0, 0]
    for (let seed = 1; seed <= 10; seed++) {
      const { score } = playToEnd(createMatch(seed))
      totals[0] += score[0]
      totals[1] += score[1]
    }
    expect(totals[0]).toBeGreaterThan(0)
    expect(totals[1]).toBeGreaterThan(0)
  })

  test('a won tackle knocks the carrier down and frees the ball', () => {
    const match = createMatch(1)
    const holder = carrier(match)!
    const tackler = match.players.find((p) => p.team !== holder.team)!
    tackler.pos = { ...holder.pos }
    tackler.strength = 1e9
    step(match)
    expect(holder.downFor).toBeGreaterThan(0)
    expect(match.ball.kind === 'loose' || carrier(match) !== holder).toBe(true)
  })

  test('a brawler who reaches an opponent off the ball fights it, and the loser goes down', () => {
    const match = createMatch(3)
    const holder = carrier(match)!
    const brawler = match.players.find((p) => p.team === holder.team && p.role === 'brawler')!
    const opponent = match.players.find((p) => p.team !== holder.team && p.role === 'runner')!
    brawler.pos = { x: 40, y: 5 }
    opponent.pos = { x: 40.5, y: 5 }
    step(match)
    expect(brawler.fight?.opponentId).toBe(opponent.id)
    expect(opponent.fight?.opponentId).toBe(brawler.id)
    for (let t = 0; t < 1.2; t += STEP_SECONDS) step(match)
    expect(brawler.fight).toBeUndefined()
    expect(brawler.downFor > 0 || opponent.downFor > 0).toBe(true)
  })

  test('a threatened carrier throws to a free runner, who catches it', () => {
    const match = createMatch(5)
    const holder = carrier(match)!
    const runner = match.players.find((p) => p.team === holder.team && p.role === 'runner')!
    for (const p of match.players) {
      if (p.team !== holder.team) p.pos = { x: holder.pos.x + 2, y: holder.pos.y }
    }
    runner.pos = { x: holder.pos.x, y: holder.pos.y + 10 }
    if (match.ball.kind === 'carried') match.ball.heldFor = 5
    step(match)
    expect(match.ball.kind).toBe('flying')
    for (let t = 0; t < 1 && match.ball.kind === 'flying'; t += STEP_SECONDS) step(match)
    expect(carrier(match)?.team).toBe(holder.team)
  })
})
