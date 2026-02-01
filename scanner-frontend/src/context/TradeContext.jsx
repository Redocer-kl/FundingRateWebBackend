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

    const setTradeParams = (params) => {
        const rawSymbol = params.symbol || '';

        const formattedSymbol = rawSymbol.toUpperCase().endsWith('USDT')
            ? rawSymbol.toUpperCase()
            : `${rawSymbol.toUpperCase()}USDT`;

        const newLong = {
            exchange: params.longExchange,
            symbol: formattedSymbol,
            amount: parseFloat(params.amount || 0),
            entryTarget: parseFloat(params.longEntry || 0),
            exitTarget: parseFloat(params.longExit || 0), 
            isExternalUpdate: true
        };

        const newShort = {
            exchange: params.shortExchange,
            symbol: formattedSymbol,
            amount: parseFloat(params.amount || 0),
            entryTarget: parseFloat(params.shortEntry || 0),
            exitTarget: parseFloat(params.shortExit || 0), 
            isExternalUpdate: true
        };

        setLongLeg(newLong);
        setShortLeg(newShort);

        console.log("TradeContext: Full state updated", { newLong, newShort });
    };

    return (
        <TradeContext.Provider value={{
            longLeg, setLongLeg,
            shortLeg, setShortLeg,
            setTradeParams
        }}>
            {children}
        </TradeContext.Provider>
    );
};