import React, { useEffect, useState, useRef, useCallback } from 'react';

const ROW_LIMIT = 15;
const CENTER_HEIGHT_PX = 32; 

const padRows = (arr) => {
    const data = Array.isArray(arr) ? arr.slice(0, ROW_LIMIT) : [];
    const rows = data.map(r => r || ['-', '-']);
    while (rows.length < ROW_LIMIT) rows.push(['-', '-']);
    return rows;
};

const OrderBook = ({ symbol, exchange = 'Binance', height = '100%' }) => {
    const [bids, setBids] = useState(() => Array.from({ length: ROW_LIMIT }, () => ['-', '-']));
    const [asks, setAsks] = useState(() => Array.from({ length: ROW_LIMIT }, () => ['-', '-']));
    const ws = useRef(null);

    const handleMessage = useCallback((event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.exchange.toLowerCase() === exchange.toLowerCase() && 
                data.symbol.toLowerCase() === symbol.toLowerCase()) {
                
                if (data.a) setAsks(padRows(data.a).reverse()); 
                if (data.b) setBids(padRows(data.b));
            }
        } catch (e) {
            console.error("WS Parse Error:", e);
        }
    }, [exchange, symbol]);

    useEffect(() => {
        let mounted = true;
        const connect = () => {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host; 
            const wsUrl = `${protocol}//${host}/ws/market/`;
            ws.current = new WebSocket(wsUrl);
            ws.current.onopen = () => {
                if (mounted && ws.current.readyState === WebSocket.OPEN) {
                    ws.current.send(JSON.stringify({
                        action: 'subscribe',
                        exchange: exchange,
                        symbol: symbol
                    }));
                }
            };
            ws.current.onmessage = handleMessage;
            ws.current.onclose = () => {
                if (mounted) setTimeout(connect, 3000);
            };
        };

        connect();
        return () => {
            mounted = false;
            if (ws.current && ws.current.readyState === WebSocket.OPEN) {
                ws.current.send(JSON.stringify({ action: 'unsubscribe', exchange, symbol }));
                ws.current.close();
            }
        };
    }, [symbol, exchange, handleMessage]);

    const topBid = (bids[0] && bids[0][0] !== '-') ? Number(bids[0][0]) : null;
    const topAsk = (asks[asks.length - 1] && asks[asks.length - 1][0] !== '-') ? Number(asks[asks.length - 1][0]) : null;
    const midPrice = (topBid && topAsk) ? ((topBid + topAsk) / 2) : (topBid || topAsk || null);


    const OrderRow = ({ price, size, colorClass }) => (
        <div className="d-flex justify-content-between px-2 py-0" style={{ lineHeight: '1.4' }}>
            <span className={colorClass}>{price !== '-' ? Number(price).toFixed(5) : '---'}</span>
            <span className="text-white-50">{size !== '-' ? Number(size).toFixed(3) : '---'}</span>
        </div>
    );

    return (
        <div className="orderbook-card bg-black text-light p-1 rounded border border-secondary border-opacity-25"
             style={{ height: height, minWidth: 200, fontFamily: "'Roboto Mono', monospace", fontSize: '11px' }}>
            
            <div className="d-flex justify-content-between align-items-center mb-1 px-1 border-bottom border-secondary border-opacity-25 pb-1">
                <span className="text-info" style={{fontSize: '10px'}}>{exchange.toUpperCase()}</span>
                <span className="fw-bold">{symbol}</span>
            </div>

            <div className="d-flex flex-column h-100 overflow-hidden">
                {/* Заголовки */}
                <div className="d-flex justify-content-between px-2 text-white-50 mb-1" style={{fontSize: '9px'}}>
                    <span>PRICE</span>
                    <span>SIZE</span>
                </div>

                {/* ASKS */}
                <div className="asks d-flex flex-column justify-content-end flex-grow-1">
                    {asks.map((a, i) => <OrderRow key={`ask-${i}`} price={a[0]} size={a[1]} colorClass="text-danger" />)}
                </div>

                {/* MID PRICE (Центр) */}
                <div className="mid-price my-1 border-top border-bottom border-secondary border-opacity-50 bg-dark bg-opacity-50" 
                     style={{ height: CENTER_HEIGHT_PX, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <span className="text-warning fw-bold" style={{ fontSize: '14px' }}>
                        {midPrice ? (typeof midPrice === 'number' ? midPrice.toFixed(5) : midPrice) : '---'}
                    </span>
                    {topBid && topAsk && (
                        <span className="text-white-50 ms-2" style={{fontSize: '9px'}}>
                            {(((topAsk - topBid) / topAsk) * 100).toFixed(3)}%
                        </span>
                    )}
                </div>

                {/* BIDS */}
                <div className="bids flex-grow-1">
                    {bids.map((b, i) => <OrderRow key={`bid-${i}`} price={b[0]} size={b[1]} colorClass="text-success" />)}
                </div>
            </div>
        </div>
    );
};

export default OrderBook;