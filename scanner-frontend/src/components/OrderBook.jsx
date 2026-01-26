import React, { useEffect, useState, useRef } from 'react';

const OrderBook = ({ symbol, title }) => {
    const [bids, setBids] = useState([]);
    const [asks, setAsks] = useState([]);
    const [price, setPrice] = useState(0);
    const ws = useRef(null);

    useEffect(() => {
        setBids([]);
        setAsks([]);

        const pair = symbol.toLowerCase();
        const wsUrl = `wss://fstream.binance.com/ws/${pair}@depth20@100ms`;

        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => {
            console.log(`Connected to ${symbol} stream`);
        };

        ws.current.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.b && data.a) {
                setBids(data.b.slice(0, 10)); 
                setAsks(data.a.slice(0, 10).reverse()); 
            }
        };


        return () => {
            if (ws.current) ws.current.close();
        };
    }, [symbol]);

    const getMaxVol = (list) => Math.max(...list.map(i => parseFloat(i[1])));
    const maxBid = getMaxVol(bids);
    const maxAsk = getMaxVol(asks);

    return (
        <div className="scanner-card p-0 border border-secondary h-100 d-flex flex-column">
            {/* Заголовок */}
            <div className="p-3 border-bottom border-secondary bg-dark d-flex justify-content-between align-items-center">
                <span className="fw-bold text-white">{title || symbol}</span>
                <span className="badge bg-warning text-dark">Binance Fut</span>
            </div>

            {/* Стакан */}
            <div className="d-flex flex-column flex-grow-1 font-mono small bg-black" style={{minHeight: '400px'}}>
                
                {/* ASKS (Продавцы - Красные) - Сверху вниз: от высоких цен к низким (ближе к рынку) */}
                <div className="d-flex flex-column justify-content-end flex-grow-1 overflow-hidden pb-1">
                    {asks.slice().reverse().map((ask, i) => { 
                        const volPercent = (parseFloat(ask[1]) / maxAsk) * 100;
                        return (
                            <div key={i} className="d-flex position-relative px-2 py-1" style={{height: '24px'}}>
                                <div className="position-absolute top-0 end-0 bottom-0 bg-danger opacity-25" style={{width: `${volPercent}%`, transition: 'width 0.1s'}}></div>
                                <span className="text-danger flex-fill text-start position-relative z-1">{parseFloat(ask[0]).toFixed(2)}</span>
                                <span className="text-light text-end position-relative z-1">{parseFloat(ask[1]).toFixed(3)}</span>
                            </div>
                        );
                    })}
                </div>

                {/* SPREAD / Current Price Placeholder */}
                <div className="py-2 border-top border-bottom border-secondary bg-secondary bg-opacity-10 text-center fw-bold text-white fs-5">
                   {bids[0] ? parseFloat(bids[0][0]).toFixed(2) : '...'} $
                </div>

                {/* BIDS (Покупатели - Зеленые) - От высоких (ближе к рынку) к низким */}
                <div className="flex-grow-1 overflow-hidden pt-1">
                    {bids.map((bid, i) => {
                        const volPercent = (parseFloat(bid[1]) / maxBid) * 100;
                        return (
                            <div key={i} className="d-flex position-relative px-2 py-1" style={{height: '24px'}}>
                                <div className="position-absolute top-0 end-0 bottom-0 bg-success opacity-25" style={{width: `${volPercent}%`, transition: 'width 0.1s'}}></div>
                                <span className="text-success flex-fill text-start position-relative z-1">{parseFloat(bid[0]).toFixed(2)}</span>
                                <span className="text-light text-end position-relative z-1">{parseFloat(bid[1]).toFixed(3)}</span>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

export default OrderBook;