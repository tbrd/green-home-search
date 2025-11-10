import { useState } from 'react';
import ListingsSearch from '../components/ListingsSearch';
import ListingsResults from '../components/ListingsResults';
import type { ListingsQuery } from '../queries/listingsQuery';

function Home() {
  const [listingsQuery, setListingsQuery] = useState<ListingsQuery>({q: null});
  const [searchTrigger, setSearchTrigger] = useState<number>(0);

  const handleListingsSearch = (query: ListingsQuery) => {
    setListingsQuery(query);
    setSearchTrigger(Date.now()); // Force a new search
  };

  return (
    <>
      <div className="bg-white rounded-lg shadow-sm p-2 mb-6">
        <ListingsSearch onSearch={handleListingsSearch} />
      </div>

      <div>
        <ListingsResults query={listingsQuery} searchTrigger={searchTrigger} pageSize={20} />
      </div>
    </>
  );
}

export default Home;
