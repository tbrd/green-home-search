import React, { useState } from 'react';
import { Button } from './ui/button';

interface SearchProps {
    onSearch: (query: {location: string; energyRating?: string}) => void;
}

const EpcSearch: React.FC<SearchProps> = ({ onSearch }) => {
    const [location, setLocation] = useState('');
    const [energyRating, setEnergyRating] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSearch({
            location,
            energyRating: energyRating || undefined,
        });
    };

    return (
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px' }}>
            <input
                type="text"
                placeholder="Postcode"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                style={{ flex: 1, padding: '8px' }}
            />
            <select style={{ padding: '8px' }} onChange={(e) => setEnergyRating(e.target.value)}>
                <option value="">Any</option>
                <option value="A">A</option>
                <option value="B">B</option>
                <option value="C">C</option>
                <option value="D">D</option>
                <option value="E">E</option>
                <option value="F">F</option>
                <option value="G">G</option>
            </select>
            <Button type="submit">
                Search
            </Button>
        </form>
    );
};

export default EpcSearch;