import './App.css'
import { useState } from 'react'
import ListingsSearch from './components/ListingsSearch'
import ListingsResults from './components/ListingsResults';
import type { ListingsQuery } from './queries/listingsQuery';

function App() {
  const [listingsQuery, setListingsQuery] = useState<ListingsQuery>({q: null});
  const [searchTrigger, setSearchTrigger] = useState<number>(0)

  const handleListingsSearch = (query: ListingsQuery) => {
    setListingsQuery(query)
    setSearchTrigger(Date.now()) // Force a new search
  }

  return (
    <div style={{ padding: 20 }}>
      <h1>Green Home Search</h1>
      
      <h2>Search Property Listings</h2>
      <ListingsSearch onSearch={handleListingsSearch} />

      <div style={{ marginTop: 20 }}>
        <ListingsResults query={listingsQuery} searchTrigger={searchTrigger} pageSize={20} />
      </div>
    </div>
  )
}

export default App
