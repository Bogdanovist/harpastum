import { describe, expect, test } from 'vitest'
import { carrier, createMatch, MATCH_SECONDS, step, STEP_SECONDS, type Match, type Player } from './match.ts'

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

  // Puts a brawler of the carrier's team and an opposing brawler in contact
  // away from the ball, with everyone else out of the way.
  function lockedPair(seed: number): { match: Match; blocker: Player; defender: Player } {
    const match = createMatch(seed)
    const holder = carrier(match)!
    const blocker = match.players.find((p) => p.team === holder.team && p.role === 'brawler')!
    const defender = match.players.find((p) => p.team !== holder.team && p.role === 'brawler')!
    for (const p of match.players) p.pos = { x: 10, y: p.team === holder.team ? 2 : 48 }
    holder.pos = { x: 20, y: 25 }
    blocker.pos = { x: 60, y: 25 }
    defender.pos = { x: 60.5, y: 25 }
    step(match)
    return { match, blocker, defender }
  }

  test('a shoving contest moves the pair back and forth until one falls or breaks free', () => {
    const { match, blocker, defender } = lockedPair(3)
    expect(blocker.shove?.opponentId).toBe(defender.id)
    expect(defender.shove?.opponentId).toBe(blocker.id)
    const start = blocker.pos.x
    let furthest = 0
    for (let t = 0; t < 20 && blocker.shove; t += STEP_SECONDS) {
      step(match)
      furthest = Math.max(furthest, Math.abs(blocker.pos.x - start))
    }
    expect(blocker.shove).toBeUndefined()
    expect(furthest).toBeGreaterThan(0.3)
    expect(blocker.downFor > 0 || defender.downFor > 0 || blocker.relockIn > 0).toBe(true)
  })

  test('a defender that drives its blocker back breaks free, and nobody falls', () => {
    const { match, blocker, defender } = lockedPair(3)
    defender.strength = 1e6
    for (let t = 0; t < 5 && defender.shove; t += STEP_SECONDS) step(match)
    expect(defender.shove).toBeUndefined()
    expect(blocker.downFor).toBe(0)
    expect(defender.relockIn).toBeGreaterThan(0)
  })

  test('a blocker that drives its defender back knocks it down', () => {
    const { match, blocker, defender } = lockedPair(3)
    blocker.strength = 1e6
    for (let t = 0; t < 5 && blocker.shove; t += STEP_SECONDS) step(match)
    expect(blocker.shove).toBeUndefined()
    expect(defender.downFor).toBeGreaterThan(0)
  })

  test('a carrier facing a wall of defenders throws forward to an open runner, who catches it', () => {
    const match = createMatch(5)
    const holder = carrier(match)!
    const runner = match.players.find((p) => p.team === holder.team && p.role === 'runner')!
    for (const p of match.players) p.pos = { x: 10, y: p.team === holder.team ? 2 : 48 }
    holder.pos = { x: 50, y: 25 }
    for (const p of match.players) if (p.team !== holder.team) p.pos = { x: 55, y: 25 }
    runner.pos = { x: 65, y: 45 }
    if (match.ball.kind === 'carried') match.ball.heldFor = 5
    step(match)
    expect(match.ball.kind).toBe('flying')
    for (let t = 0; t < 2 && match.ball.kind === 'flying'; t += STEP_SECONDS) step(match)
    expect(carrier(match)).toBe(runner)
  })

  test('a carrier with a clear run to the line keeps the ball, even with a chaser close behind', () => {
    const match = createMatch(5)
    const holder = carrier(match)!
    const back = match.players.find((p) => p.team === holder.team && p.role === 'back')!
    for (const p of match.players) p.pos = { x: 50, y: p.team === holder.team ? 2 : 48 }
    holder.pos = { x: 80, y: 25 }
    back.pos = { x: 70, y: 25 }
    // A slower chaser just behind the carrier can never catch it.
    const chaser = match.players.find((p) => p.team !== holder.team)!
    chaser.pos = { x: 78, y: 26 }
    chaser.speed = 4
    holder.speed = 7
    if (match.ball.kind === 'carried') match.ball.heldFor = 5
    step(match)
    expect(carrier(match)).toBe(holder)
  })

  test('a defender pressed against the thrower cannot catch the ball as it leaves the hand', () => {
    const match = createMatch(5)
    const thrower = carrier(match)!
    const defender = match.players.find((p) => p.team !== thrower.team)!
    for (const p of match.players) if (p !== thrower) p.pos = { x: 10, y: 45 }
    thrower.pos = { x: 50, y: 25 }
    defender.pos = { x: 50.5, y: 25 }
    match.ball = { kind: 'flying', pos: { ...thrower.pos }, from: { ...thrower.pos }, landAt: { x: 60, y: 25 }, throwerId: thrower.id }
    step(match)
    expect(match.ball.kind).toBe('flying')
  })
})
