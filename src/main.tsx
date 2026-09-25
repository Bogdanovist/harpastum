import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { TitleScreen } from './TitleScreen.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <TitleScreen />
  </StrictMode>,
)
