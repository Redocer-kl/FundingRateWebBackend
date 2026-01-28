import React, { useEffect, useState, useRef, useMemo, useCallback } from 'react';

const OrderBook = ({ symbol, exchange = 'Binance' }) => {
    const [bids, setBids] = useState([]);
    const [asks, setAsks] = useState([]);
    const [status, setStatus] = useState('CONNECTING');
    
    const orderBookRef = useRef({ bids: {}, asks: {} });
    const ws = useRef(null);
    const ROW_LIMIT = 15;

    // Конфиги (оставил твои, только поправил Hyperliquid для стабильности)
    const EXCHANGE_CONFIGS = useMemo(() => ({
        'Binance': {
            url: (s) => `wss://fstream.binance.com/ws/${s.toLowerCase()}@depth20@100ms`,
            shouldMerge: false, 
            format: (data) => ({ b: data.b, a: data.a })
        },
        'Bitget': {
            url: () => `wss://ws.bitget.com/v2/ws/public`,
            subscribe: (s) => ({
                op: 'subscribe',
                args: [{ instType: 'USDT-FUTURES', channel: 'books15', instId: s.toUpperCase() }]
            }),
            shouldMerge: false, 
            format: (data) => (data.action === 'snapshot' || data.action === 'update') ? { b: data.data?.[0]?.bids, a: data.data?.[0]?.asks } : null
        },
        'Bybit': {
            url: () => `wss://stream.bybit.com/v5/public/linear`,
            subscribe: (s) => ({ op: "subscribe", args: [`orderbook.50.${s.toUpperCase()}`] }),
            shouldMerge: true, 
            format: (data) => data.data ? { b: data.data.b, a: data.data.a, type: data.type } : null
        },
        'Hyperliquid': {
            url: () => `wss://api.hyperliquid.xyz/ws`,
            subscribe: (s) => ({ method: "subscribe", subscription: { type: "l2Book", coin: s.replace('USDT', '') } }),
            shouldMerge: false, 
            format: (data) => (data.channel === 'l2Book' && data.data) ? { b: data.data.levels[0].map(l => [l.px, l.sz]), a: data.data.levels[1].map(l => [l.px, l.sz]) } : null
        },
        'CoinEx': {
            url: () => `wss://perpetual.coinex.com/`,
            subscribe: (s) => ({
                method: "depth.subscribe",
                params: [s.toUpperCase(), 20, "0", true],
                id: 1
            }),
            shouldMerge: false,
            format: (data) => {
                // CoinEx присылает данные в поле params
                if (data.method === 'depth.update' && data.params) {
                    const [isFull, depth, symbol] = data.params;
                    return { b: depth.bids, a: depth.asks };
                }
                return null;
            }
        },
    }), []);

    const updateOrderBook = useCallback((newData, type, isSnapshot) => {
        const currentBook = orderBookRef.current;
        if (isSnapshot) {
            currentBook.bids = {}; currentBook.asks = {};
            newData.b?.forEach(([p, s]) => { currentBook.bids[p] = s; });
            newData.a?.forEach(([p, s]) => { currentBook.asks[p] = s; });
        } else {
            newData.b?.forEach(([p, s]) => { if (parseFloat(s) === 0) delete currentBook.bids[p]; else currentBook.bids[p] = s; });
            newData.a?.forEach(([p, s]) => { if (parseFloat(s) === 0) delete currentBook.asks[p]; else currentBook.asks[p] = s; });
        }

        const sortedBids = Object.entries(currentBook.bids).sort((a, b) => parseFloat(b[0]) - parseFloat(a[0])).slice(0, ROW_LIMIT);
        const sortedAsks = Object.entries(currentBook.asks).sort((a, b) => parseFloat(a[0]) - parseFloat(b[0])).slice(0, ROW_LIMIT).reverse(); 

        setBids(sortedBids);
        setAsks(sortedAsks);
    }, []);

    useEffect(() => {
        const config = EXCHANGE_CONFIGS[exchange];
        if (!config) return;
        const pair = symbol.toUpperCase();
        setBids([]); setAsks([]);
        orderBookRef.current = { bids: {}, asks: {} };
        setStatus('CONNECTING');

        const connect = () => {
            if (ws.current) ws.current.close();
            ws.current = new WebSocket(config.url(pair));
            ws.current.onopen = () => {
                setStatus('ONLINE');
                if (config.subscribe && ws.current.readyState === 1) ws.current.send(JSON.stringify(config.subscribe(pair)));
            };
            ws.current.onmessage = (e) => {
                if (e.data === 'ping') { ws.current.send('pong'); return; }
                const data = JSON.parse(e.data);
                if (data.op === 'ping') { ws.current.send(JSON.stringify({ op: 'pong' })); return; }
                const parsed = config.format(data);
                if (!parsed) return;
                if (config.shouldMerge) updateOrderBook(parsed, parsed.type, parsed.type === 'snapshot');
                else {
                    if (parsed.b) setBids(parsed.b.slice(0, ROW_LIMIT));
                    if (parsed.a) setAsks(parsed.a.slice(0, ROW_LIMIT).reverse());
                }
            };
            ws.current.onerror = () => setStatus('ERROR');
            ws.current.onclose = () => setStatus('OFFLINE');
        };
        connect();
        return () => ws.current?.close();
    }, [symbol, exchange, EXCHANGE_CONFIGS, updateOrderBook]);

    const maxVol = useMemo(() => {
        const vals = [...bids.map(b => b[1]), ...asks.map(a => a[1])].map(v => parseFloat(v));
        return vals.length ? Math.max(...vals) : 1;
    }, [bids, asks]);

    return (
        <div className="orderbook-container bg-black border border-secondary d-flex flex-column h-100 shadow-sm" style={{ fontFamily: 'monospace', borderRadius: '4px', overflow: 'hidden' }}>
            <div className="p-2 bg-dark border-bottom border-secondary d-flex justify-content-between align-items-center">
                <span className="fw-bold text-light small" style={{fontSize: '11px'}}>
                   {status === 'ONLINE' ? '🟢' : status === 'ERROR' ? '🔴' : '🟡'} {exchange}
                </span>
                <span className="text-info" style={{ fontSize: '10px' }}>{symbol}</span>
            </div>

            {/* ASKS (Sellers) - Высота фиксирована через flex-basis */}
            <div className="asks-section d-flex flex-column justify-content-end flex-grow-1 overflow-hidden" style={{ minHeight: 0 }}>
                {asks.map((a, i) => (
                    <div key={i} className="px-2 position-relative d-flex justify-content-between align-items-center" style={{ height: '20px', fontSize: '12px' }}>
                        <div className="position-absolute top-0 end-0 bottom-0 bg-danger" 
                             style={{ width: `${(parseFloat(a[1]) / maxVol) * 100}%`, opacity: 0.15, zIndex: 0 }} />
                        <span className="text-danger z-1">{parseFloat(a[0])}</span>
                        <span className="text-light opacity-75 z-1">{parseFloat(a[1]).toFixed(3)}</span>
                    </div>
                ))}
            </div>

            {/* Spread */}
            <div className="py-1 bg-secondary bg-opacity-25 text-center fw-bold text-warning border-top border-bottom border-secondary" style={{fontSize: '14px'}}>
                {bids[0] ? parseFloat(bids[0][0]) : '---'}
            </div>

            {/* BIDS (Buyers) */}
            <div className="bids-section flex-grow-1 overflow-hidden" style={{ minHeight: 0 }}>
                {bids.map((b, i) => (
                    <div key={i} className="px-2 position-relative d-flex justify-content-between align-items-center" style={{ height: '20px', fontSize: '12px' }}>
                        <div className="position-absolute top-0 end-0 bottom-0 bg-success" 
                             style={{ width: `${(parseFloat(b[1]) / maxVol) * 100}%`, opacity: 0.15, zIndex: 0 }} />
                        <span className="text-success z-1">{parseFloat(b[0])}</span>
                        <span className="text-light opacity-75 z-1">{parseFloat(b[1]).toFixed(3)}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default OrderBook;