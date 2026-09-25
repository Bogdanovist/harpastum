import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'
import { TitleScreen } from './TitleScreen.tsx'

test('shows the game title', () => {
  render(<TitleScreen onPlay={() => {}} />)
  expect(screen.getByRole('heading', { name: 'Harpastum' })).toBeDefined()
})
