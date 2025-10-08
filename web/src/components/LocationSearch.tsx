import React, { useState } from 'react';

interface SearchProps {
    onSearch: (location: string) => void;
}

const LocationSearch: React.FC<SearchProps> = ({ onSearch }) => {
    const [location, setLocation] = useState('');

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setLocation(e.target.value);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSearch(location);
    };

    return (
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px' }}>
            <input
                type="text"
                placeholder="Enter location"
                value={location}
                onChange={handleInputChange}
                style={{ flex: 1, padding: '8px' }}
            />
            <button type="submit" style={{ padding: '8px 16px' }}>
                Search
            </button>
        </form>
    );
};

export default LocationSearch;