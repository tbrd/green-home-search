import './App.css'
import { useState } from 'react'
import LocationSearch from './components/LocationSearch'
import SearchResults from './components/SearchResults'

function App() {
  const [query, setQuery] = useState<{location: string | null, energyRating?: string}>({location: null});
  const [searchTrigger, setSearchTrigger] = useState<number>(0)

  const handleSearch = ({location, energyRating}: {location: string | null, energyRating?: string}) => {
    setQuery({location, energyRating})
    setSearchTrigger(Date.now()) // Force a new search even if location is the same
  }

  return (
    <div style={{ padding: 20 }}>
      <h1>Green Home Search</h1>
      <LocationSearch onSearch={handleSearch} />


      <div style={{ marginTop: 20 }}>
        <SearchResults query={query} searchTrigger={searchTrigger} />
      </div>
    </div>
  )
}

export default App
