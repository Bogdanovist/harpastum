import { useEffect, useRef, useState } from 'react'
import { CANVAS_HEIGHT, CANVAS_WIDTH, drawMatch } from './render/drawMatch.ts'
import { createMatch, MATCH_SECONDS, step, STEP_SECONDS, type Match } from './sim/match.ts'
import './MatchScreen.css'

const SPEEDS = [1, 2, 4]
// Cap the catch-up after the tab was in the background, so returning to it
// does not freeze the page while the sim runs minutes of play at once.
const MAX_FRAME_SECONDS = 0.25

interface Scoreboard {
  score: [number, number]
  secondsLeft: number
  ended: boolean
}

function readScoreboard(match: Match): Scoreboard {
  return {
    score: [match.score[0], match.score[1]],
    secondsLeft: Math.max(0, Math.ceil(MATCH_SECONDS - match.clock)),
    ended: match.phase.kind === 'ended',
  }
}

const KICK_OFF_SCOREBOARD: Scoreboard = { score: [0, 0], secondsLeft: MATCH_SECONDS, ended: false }

const sameScoreboard = (a: Scoreboard, b: Scoreboard) =>
  a.score[0] === b.score[0] && a.score[1] === b.score[1] && a.secondsLeft === b.secondsLeft && a.ended === b.ended

const newSeed = () => Math.floor(Math.random() * 1_000_000)

function formatClock(seconds: number): string {
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`
}

export function MatchScreen() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [seed, setSeed] = useState(newSeed)
  const [paused, setPaused] = useState(false)
  const [speed, setSpeed] = useState(1)
  const matchRef = useRef<Match>(createMatch(seed))
  const [scoreboard, setScoreboard] = useState<Scoreboard>(KICK_OFF_SCOREBOARD)
  const controlsRef = useRef({ paused, speed })
  useEffect(() => {
    controlsRef.current = { paused, speed }
  }, [paused, speed])

  function startNewMatch() {
    const next = newSeed()
    matchRef.current = createMatch(next)
    setSeed(next)
    setPaused(false)
    setScoreboard(readScoreboard(matchRef.current))
  }

  useEffect(() => {
    const ctx = canvasRef.current?.getContext('2d')
    if (!ctx) return
    let frame = 0
    let last = performance.now()
    let owed = 0
    const tick = (now: number) => {
      const { paused, speed } = controlsRef.current
      const match = matchRef.current
      if (!paused) owed += Math.min(MAX_FRAME_SECONDS, (now - last) / 1000) * speed
      last = now
      while (owed >= STEP_SECONDS) {
        step(match)
        owed -= STEP_SECONDS
      }
      drawMatch(ctx, match)
      const next = readScoreboard(match)
      setScoreboard((prev) => (sameScoreboard(prev, next) ? prev : next))
      frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [])

  const nextSpeed = SPEEDS[(SPEEDS.indexOf(speed) + 1) % SPEEDS.length]

  return (
    <main className="match-screen">
      <header className="scoreboard">
        <span className="team team-0">RED {scoreboard.score[0]}</span>
        <span className="clock">{scoreboard.ended ? 'FULL TIME' : formatClock(scoreboard.secondsLeft)}</span>
        <span className="team team-1">{scoreboard.score[1]} BLUE</span>
      </header>
      <p className="seed">seed {seed}</p>
      <canvas ref={canvasRef} width={CANVAS_WIDTH} height={CANVAS_HEIGHT} />
      <nav className="controls">
        <button type="button" onClick={() => setPaused((p) => !p)}>
          {paused ? 'Play' : 'Pause'}
        </button>
        <button type="button" onClick={() => setSpeed(nextSpeed)}>
          {speed}×
        </button>
        <button type="button" onClick={startNewMatch}>
          New match
        </button>
      </nav>
    </main>
  )
}
