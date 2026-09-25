import './TitleScreen.css'

export function TitleScreen() {
  return (
    <main className="title-screen">
      <h1>Harpastum</h1>
      <p className="tagline">Rome, Greece and the Celts take the field.</p>
      <button type="button" disabled>
        New season
      </button>
    </main>
  )
}
