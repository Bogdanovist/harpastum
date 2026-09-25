import { describe, expect, test } from 'vitest'
import { carrier, createMatch, MATCH_SECONDS, step, type Match } from './match.ts'

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
})
