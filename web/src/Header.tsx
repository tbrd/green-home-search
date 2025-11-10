/// <reference types="vite-plugin-svgr/client" />
import Logo from "./assets/Hearthwise.svg?react";

export default function Header() {
    return (
        <header >
            <nav className="flex justify-between py-4">
                <div className="flex flex-col">
                    <div><Logo className="h-7" /></div>
                    <p className="text-gray-600 text-sm">Homes for your budget</p>
                </div>
            </nav>
        </header>
    );
}