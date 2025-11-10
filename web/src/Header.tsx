/// <reference types="vite-plugin-svgr/client" />
import { Link } from 'react-router-dom';
import Logo from "./assets/Hearthwise.svg?react";
import { Button } from './components/ui/button';

export default function Header() {
    return (
        <header >
            <nav className="flex justify-between py-4">
                <Link to="/" className="flex flex-col">
                    <div><Logo className="h-7" /></div>
                    <p className="text-gray-600 text-sm">Homes for your budget</p>
                </Link>
                <div className="flex items-center">
                    <Link to="/profile">
                        <Button variant="outline" size="sm">
                            Profile
                        </Button>
                    </Link>
                </div>
            </nav>
        </header>
    );
}