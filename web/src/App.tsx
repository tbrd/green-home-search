import './App.css'
import { useState } from 'react'
import LocationSearch from './components/LocationSearch'
import ListingsResults from './components/ListingsResults';
import { Button } from '@/components/ui/button';

function App() {
  const [query, setQuery] = useState<{q: string | null, energyRating?: string}>({q: null});
  const [searchTrigger, setSearchTrigger] = useState<number>(0)

  const handleSearch = ({location, energyRating}: {location: string | null, energyRating?: string}) => {
    setQuery({q: location, energyRating})
    setSearchTrigger(Date.now()) // Force a new search even if location is the same
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Green Home Search</h1>
          <p className="text-gray-600">Find energy-efficient homes in the UK</p>
        </div>

        {/* Button Showcase */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">Button Components</h2>
          <div className="flex flex-wrap gap-4">
            <Button>Default Button</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="destructive">Destructive</Button>
            <Button variant="link">Link</Button>
          </div>
          <div className="flex flex-wrap gap-4 mt-4">
            <Button size="sm">Small</Button>
            <Button size="default">Default</Button>
            <Button size="lg">Large</Button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <LocationSearch onSearch={handleSearch} />
        </div>

        <div>
          <ListingsResults query={query} searchTrigger={searchTrigger} pageSize={20} />
        </div>
      </div>
    </div>
  )
}

export default App
