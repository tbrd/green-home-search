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
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Green Home Search</h1>
          <p className="text-gray-600">Find energy-efficient homes in the UK</p>
        </div>

        
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <ListingsSearch onSearch={handleListingsSearch} />
        </div>

        <div>
          <ListingsResults query={listingsQuery} searchTrigger={searchTrigger} pageSize={20} />
        </div>

      </div>
    </div>
  )
}

export default App
