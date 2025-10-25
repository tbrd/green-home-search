import React, { useState } from 'react';
import type { ListingsQuery } from '../queries/listingsQuery';

interface ListingsSearchProps {
    onSearch: (query: ListingsQuery) => void;
}

const ListingsSearch: React.FC<ListingsSearchProps> = ({ onSearch }) => {
    const [q, setQ] = useState('');
    const [minPrice, setMinPrice] = useState('');
    const [maxPrice, setMaxPrice] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        
        // Parse and validate price inputs
        const parsedMinPrice = minPrice ? parseFloat(minPrice) : null;
        const parsedMaxPrice = maxPrice ? parseFloat(maxPrice) : null;
        
        const query: ListingsQuery = {
            q: q || null,
            minPrice: parsedMinPrice !== null && !isNaN(parsedMinPrice) ? parsedMinPrice : null,
            maxPrice: parsedMaxPrice !== null && !isNaN(parsedMaxPrice) ? parsedMaxPrice : null,
        };
        
        onSearch(query);
    };

    return (
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <input
                type="text"
                placeholder="Postcode or address"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                style={{ flex: 1, minWidth: '200px', padding: '8px' }}
            />
            <input
                type="number"
                placeholder="Min price (£)"
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value)}
                style={{ width: '150px', padding: '8px' }}
                min="0"
                step="1000"
            />
            <input
                type="number"
                placeholder="Max price (£)"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                style={{ width: '150px', padding: '8px' }}
                min="0"
                step="1000"
            />
            <button type="submit" style={{ padding: '8px 16px' }}>
                Search Listings
            </button>
        </form>
    );
};

export default ListingsSearch;
