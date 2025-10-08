import './App.css'
import { useState } from 'react'
import LocationSearch from './components/LocationSearch'
import SearchResults from './components/SearchResults'

function App() {
  const [query, setQuery] = useState<string | null>(null)

  return (
    <div style={{ padding: 20 }}>
      <h1>Green Home Search</h1>
      <LocationSearch onSearch={(location) => setQuery(location || null)} />

      <div style={{ marginTop: 12, display: 'flex', gap: 8, alignItems: 'center' }}>
        <label style={{ fontSize: 14 }}>Radius (meters):</label>
      </div>

      <div style={{ marginTop: 20 }}>
        <SearchResults query={query} />
      </div>
    </div>
  )
}

export default App
