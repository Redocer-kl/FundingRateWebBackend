import { createContext, useState, useEffect } from 'react';

export const TradeContext = createContext();

export const TradeProvider = ({ children }) => {
    const [longLeg, setLongLeg] = useState(() => {
        const saved = localStorage.getItem('longLeg');
        return saved ? JSON.parse(saved) : null;
    });

    const [shortLeg, setShortLeg] = useState(() => {
        const saved = localStorage.getItem('shortLeg');
        return saved ? JSON.parse(saved) : null;
    });

    useEffect(() => {
        if (longLeg) localStorage.setItem('longLeg', JSON.stringify(longLeg));
    }, [longLeg]);

    useEffect(() => {
        if (shortLeg) localStorage.setItem('shortLeg', JSON.stringify(shortLeg));
    }, [shortLeg]);


    useEffect(() => {
        console.log("Current Trade State:", { longLeg, shortLeg });
    }, [longLeg, shortLeg]);

    return (
        <TradeContext.Provider value={{ longLeg, setLongLeg, shortLeg, setShortLeg }}>
            {children}
        </TradeContext.Provider>
    );
};