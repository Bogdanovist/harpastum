// Mulberry32: a small seeded generator. The whole match must replay from its
// seed, so the sim draws every random number from here, never Math.random.
export function nextRandom(state: { rngState: number }): number {
  state.rngState = (state.rngState + 0x6d2b79f5) | 0
  let t = state.rngState
  t = Math.imul(t ^ (t >>> 15), t | 1)
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296
}
