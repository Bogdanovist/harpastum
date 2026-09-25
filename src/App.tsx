import { useState } from 'react'
import { MatchScreen } from './MatchScreen.tsx'
import { TitleScreen } from './TitleScreen.tsx'

export function App() {
  const [playing, setPlaying] = useState(false)
  return playing ? <MatchScreen /> : <TitleScreen onPlay={() => setPlaying(true)} />
}
