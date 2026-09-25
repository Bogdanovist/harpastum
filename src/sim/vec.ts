export interface Vec {
  x: number
  y: number
}

export const add = (a: Vec, b: Vec): Vec => ({ x: a.x + b.x, y: a.y + b.y })
export const sub = (a: Vec, b: Vec): Vec => ({ x: a.x - b.x, y: a.y - b.y })
export const scale = (a: Vec, k: number): Vec => ({ x: a.x * k, y: a.y * k })
export const length = (a: Vec): number => Math.hypot(a.x, a.y)
export const distance = (a: Vec, b: Vec): number => Math.hypot(a.x - b.x, a.y - b.y)

export function normalize(a: Vec): Vec {
  const len = length(a)
  return len === 0 ? { x: 0, y: 0 } : { x: a.x / len, y: a.y / len }
}

export function clampLength(a: Vec, max: number): Vec {
  const len = length(a)
  return len <= max ? a : scale(a, max / len)
}
