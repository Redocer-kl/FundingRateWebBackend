import React, { useEffect, useRef, useState, useMemo } from 'react';
import { createChart, ColorType, CrosshairMode, CandlestickSeries } from 'lightweight-charts';
// Импортируем твой настроенный инстанс
import api from '../api'; 

const CandleChart = ({ symbol, exchange = 'Binance' }) => {
    const chartContainerRef = useRef();
    const chartRef = useRef(null);
    const seriesRef = useRef(null);
    const wsRef = useRef(null);
    const [isLoading, setIsLoading] = useState(true);

    // Конфигурации парсинга данных (оставляем, так как ответ от прокси будет сырым ответом биржи)
    const CONFIG = useMemo(() => ({
        'Binance': {
            ws: (s) => `wss://fstream.binance.com/ws/${s.toLowerCase()}@kline_1m`,
            parseHistory: (d) => d.map(k => ({ time: k[0] / 1000, open: parseFloat(k[1]), high: parseFloat(k[2]), low: parseFloat(k[3]), close: parseFloat(k[4]) })),
            parseWS: (msg) => msg.k ? { time: msg.k.t / 1000, open: parseFloat(msg.k.o), high: parseFloat(msg.k.h), low: parseFloat(msg.k.l), close: parseFloat(msg.k.c) } : null
        },
        'Bitget': {
            ws: () => `wss://ws.bitget.com/v2/ws/public`,
            subscribe: (s) => ({ op: "subscribe", args: [{ instType: "mc", channel: "candle1m", instId: s.toUpperCase() }] }),
            parseHistory: (d) => (d.data || []).map(k => ({ time: parseInt(k[0]) / 1000, open: parseFloat(k[1]), high: parseFloat(k[2]), low: parseFloat(k[3]), close: parseFloat(k[4]) })),
            parseWS: (msg) => msg.data ? { time: parseInt(msg.data[0][0]) / 1000, open: parseFloat(msg.data[0][1]), high: parseFloat(msg.data[0][2]), low: parseFloat(msg.data[0][3]), close: parseFloat(msg.data[0][4]) } : null
        },
        'Kucoin': {
            ws: () => `wss://api-futures.kucoin.com/api/v1/connection`, 
            subscribe: (s) => ({ id: Date.now(), type: 'subscribe', topic: `/contractMarket/limitCandle:${s.toUpperCase()}_1min` }),
            parseHistory: (d) => (d.data || []).map(k => ({ time: k[0] / 1000, open: parseFloat(k[1]), high: parseFloat(k[2]), low: parseFloat(k[3]), close: parseFloat(k[4]) })),
            parseWS: (msg) => msg.data ? { time: msg.data.cycles[0] / 1000, open: parseFloat(msg.data.candles[0]), high: parseFloat(msg.data.candles[1]), low: parseFloat(msg.data.candles[2]), close: parseFloat(msg.data.candles[3]) } : null
        },
        'CoinEx': {
            ws: () => `wss://socket.coinex.com/`,
            subscribe: (s) => ({ method: "kline.subscribe", params: [s.toUpperCase(), 60], id: 1 }),
            parseHistory: (d) => (d.data || []).map(k => ({ time: k[0], open: parseFloat(k[1]), high: parseFloat(k[3]), low: parseFloat(k[4]), close: parseFloat(k[2]) })),
            parseWS: (msg) => (msg.method === "kline.update") ? { time: msg.params[0][0], open: parseFloat(msg.params[0][1]), high: parseFloat(msg.params[0][3]), low: parseFloat(msg.params[0][4]), close: parseFloat(msg.params[0][2]) } : null
        },
        'Paradex': {
            ws: () => `wss://ws.api.paradex.trade/v1`,
            subscribe: (s) => ({ method: "subscribe", params: { channel: `candles.1.${s.toUpperCase().replace('USDT', '-USD')}` } }),
            parseHistory: (d) => (d.results || []).map(k => ({ time: k[0] / 1000, open: parseFloat(k[1]), high: parseFloat(k[2]), low: parseFloat(k[3]), close: parseFloat(k[4]) })),
            parseWS: (msg) => (msg.channel?.startsWith('candles')) ? { time: msg.data.t / 1000, open: parseFloat(msg.data.o), high: parseFloat(msg.data.h), low: parseFloat(msg.data.l), close: parseFloat(msg.data.c) } : null
        },
        'Hyperliquid': {
            ws: () => `wss://api.hyperliquid.xyz/ws`,
            subscribe: (s) => ({ method: "subscribe", subscription: { type: "candle", coin: s.toUpperCase().replace('USDT', ''), interval: "1m" } }),
            parseHistory: (d) => (d || []).map(k => ({ time: k.t / 1000, open: parseFloat(k.o), high: parseFloat(k.h), low: parseFloat(k.l), close: parseFloat(k.c) })),
            parseWS: (msg) => (msg.channel === "candle" && msg.data) ? { time: msg.data.t / 1000, open: parseFloat(msg.data.o), high: parseFloat(msg.data.h), low: parseFloat(msg.data.l), close: parseFloat(msg.data.c) } : null
        }
    }), []);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            layout: { background: { type: ColorType.Solid, color: '#000000' }, textColor: '#d1d4dc' },
            grid: { vertLines: { color: '#1f1f1f' }, horzLines: { color: '#1f1f1f' } },
            crosshair: { mode: CrosshairMode.Normal },
            timeScale: { borderColor: '#333', timeVisible: true },
            height: 300,
        });

        const candlestickSeries = chart.addSeries(CandlestickSeries, {
            upColor: '#26a69a', downColor: '#ef5350', borderVisible: false,
            wickUpColor: '#26a69a', wickDownColor: '#ef5350',
        });

        chartRef.current = chart;
        seriesRef.current = candlestickSeries;

        const loadData = async () => {
            setIsLoading(true);
            const pair = symbol.toUpperCase();
            const exCfg = CONFIG[exchange] || CONFIG['Binance'];

            try {
                // Используем твой api.js для проксирования
                // Путь 'proxy/kline/' должен соответствовать твоему urls.py в Django
                const res = await api.get('proxy/kline/', {
                    params: {
                        exchange: exchange,
                        symbol: pair,
                        interval: exchange === 'CoinEx' ? '1min' : '1m', // Небольшой фикс для нейминга интервалов
                        limit: 150
                    }
                });

                const formatted = exCfg.parseHistory(res.data);
                
                if (formatted && formatted.length > 0) {
                    candlestickSeries.setData(formatted);
                    chart.timeScale().fitContent();
                }

                // WebSocket (прямое соединение)
                if (wsRef.current) wsRef.current.close();
                const wsUrl = exCfg.ws(pair);
                
                if (wsUrl) {
                    wsRef.current = new WebSocket(wsUrl);
                    wsRef.current.onopen = () => {
                        if (wsRef.current?.readyState === WebSocket.OPEN && exCfg.subscribe) {
                            wsRef.current.send(JSON.stringify(exCfg.subscribe(pair)));
                        }
                    };
                    wsRef.current.onmessage = (event) => {
                        try {
                            const msg = JSON.parse(event.data);
                            const updated = exCfg.parseWS(msg);
                            if (updated) candlestickSeries.update(updated);
                        } catch (e) {}
                    };
                }

            } catch (err) {
                console.error(`[${exchange}] Chart Error:`, err);
            } finally {
                setIsLoading(false);
            }
        };

        loadData();

        const handleResize = () => chart.applyOptions({ width: chartContainerRef.current.clientWidth });
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            if (wsRef.current) wsRef.current.close();
            chart.remove();
        };
    }, [symbol, exchange, CONFIG]);

    return (
        <div className="position-relative bg-black border border-secondary mb-3 rounded shadow-sm">
            <div className="p-2 border-bottom border-secondary d-flex justify-content-between align-items-center bg-dark bg-opacity-50">
                <span className="fw-bold text-white small">
                    {symbol} <span className="text-primary opacity-75">{exchange}</span>
                </span>
                <span className="badge bg-secondary opacity-50" style={{fontSize: '10px'}}>1m</span>
            </div>
            <div ref={chartContainerRef} style={{ width: '100%', height: '300px' }} />
            {isLoading && (
                <div className="position-absolute top-50 start-50 translate-middle">
                    <div className="spinner-border spinner-border-sm text-primary" role="status"></div>
                </div>
            )}
        </div>
    );
};

export default CandleChart;