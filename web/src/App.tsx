import './App.css'
import { useState } from 'react'
import LocationSearch from './components/LocationSearch'
import ListingsResults from './components/ListingsResults';

function App() {
  const [query, setQuery] = useState<{q: string | null, energyRating?: string}>({q: null});
  const [searchTrigger, setSearchTrigger] = useState<number>(0)

  const handleSearch = ({location, energyRating}: {location: string | null, energyRating?: string}) => {
    setQuery({q: location, energyRating})
    setSearchTrigger(Date.now()) // Force a new search even if location is the same
  }

  return (
    <div style={{ padding: 20 }}>
      <h1>Green Home Search</h1>
      <LocationSearch onSearch={handleSearch} />


      <div style={{ marginTop: 20 }}>
        <ListingsResults query={query} searchTrigger={searchTrigger} pageSize={20} />


      </div>
    </div>
  )
}

export default App
