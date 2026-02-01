import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, CandlestickSeries, LineStyle } from 'lightweight-charts';
import api from '../api';

const normTime = (t) => {
  const n = Number(t);
  if (!isFinite(n) || n <= 0) return 0;
  if (n > 1e11) return Math.floor(n / 1000);
  if (n > 1e9) return Math.floor(n);
  return Math.floor(n);
};

const CONFIG = {
  Binance: {
    getWsUrl: async (s) => `wss://stream.binance.com:9443/ws/${s.toLowerCase()}@kline_1m`,
    parseHistory: (d) => (d || []).map(k => ({ time: normTime(k[0]), open: parseFloat(k[1]), high: parseFloat(k[2]), low: parseFloat(k[3]), close: parseFloat(k[4]) })),
    parseWS: (msg) => (msg?.k ? ({ time: normTime(msg.k.t), open: parseFloat(msg.k.o), high: parseFloat(msg.k.h), low: parseFloat(msg.k.l), close: parseFloat(msg.k.c) }) : null)
  },
  Paradex: {
    getWsUrl: async () => `wss://ws.api.prod.paradex.trade/v1`,
    subscribe: (s) => ({ jsonrpc: "2.0", method: "subscribe", params: { channel: "candles", market: s.replace('USDT', '-USD-PERP'), resolution: "1" }, id: Date.now() }),
    parseHistory: (d) => {
      if (d && d.t) return d.t.map((time, i) => ({ time: normTime(time), open: parseFloat(d.o[i]), high: parseFloat(d.h[i]), low: parseFloat(d.l[i]), close: parseFloat(d.c[i]) }));
      return [];
    },
    parseWS: (msg) => {
      if (msg.params?.data && msg.params.channel === 'candles') {
        const dd = msg.params.data;
        return { time: normTime(dd.t), open: parseFloat(dd.o), high: parseFloat(dd.h), low: parseFloat(dd.l), close: parseFloat(dd.c) };
      }
      return null;
    }
  },
  Kucoin: {
    getWsUrl: async (s, tokenFunc) => await tokenFunc(),
    subscribe: (s) => ({ type: 'subscribe', topic: `/contractMarket/limitCandle:${s.toUpperCase()}M_1min`, id: Date.now() }),
    parseHistory: (d) => (d.data || []).map(k => ({ time: normTime(k[0]), open: parseFloat(k[1]), high: parseFloat(k[2]), low: parseFloat(k[3]), close: parseFloat(k[4]) })).sort((a,b)=>a.time-b.time),
    parseWS: (msg) => {
      if (msg.type === 'message' && msg.data && msg.data.candles) {
        const c = msg.data.candles;
        return { time: normTime(c[0]), open: parseFloat(c[1]), high: parseFloat(c[2]), low: parseFloat(c[3]), close: parseFloat(c[4]) };
      }
      return null;
    }
  },
  Bitget: {
    getWsUrl: async () => `wss://ws.bitget.com/v2/ws/public`,
    subscribe: (s) => ({ op: "subscribe", args: [{ instType: "mc", channel: "candle1m", instId: s.toUpperCase() }] }),
    parseHistory: (d) => (d.data || []).map(k => ({ time: normTime(k[0]), open: parseFloat(k[1]), high: parseFloat(k[2]), low: parseFloat(k[3]), close: parseFloat(k[4]) })),
    parseWS: (msg) => (msg.data && Array.isArray(msg.data[0])) ? ({ time: normTime(parseInt(msg.data[0][0])), open: parseFloat(msg.data[0][1]), high: parseFloat(msg.data[0][2]), low: parseFloat(msg.data[0][3]), close: parseFloat(msg.data[0][4]) }) : null
  },
  Hyperliquid: {
    getWsUrl: async () => `wss://api.hyperliquid.xyz/ws`,
    subscribe: (s) => ({ method: "subscribe", subscription: { type: "candle", coin: s.toUpperCase().replace('USDT',''), interval: "1m" } }),
    parseHistory: (d) => (d || []).map(k => ({ time: normTime(k.t), open: parseFloat(k.o), high: parseFloat(k.h), low: parseFloat(k.l), close: parseFloat(k.c) })).sort((a,b)=>a.time-b.time),
    parseWS: (msg) => (msg.channel === "candle" && msg.data) ? ({ time: normTime(msg.data.t), open: parseFloat(msg.data.o), high: parseFloat(msg.data.h), low: parseFloat(msg.data.l), close: parseFloat(msg.data.c) }) : null
  },
  CoinEx: {
    getWsUrl: async () => `wss://socket.coinex.com/`,
    subscribe: (s) => ({ method: "kline.subscribe", params: [s.toUpperCase(), 60], id: 1 }),
    parseHistory: (d) => (d.data || []).map(k => ({ time: normTime(k[0]), open: parseFloat(k[1]), high: parseFloat(k[3]), low: parseFloat(k[4]), close: parseFloat(k[2]) })),
    parseWS: (msg) => (msg.method === "kline.update" && msg.params?.[0]) ? ({ time: normTime(msg.params[0][0]), open: parseFloat(msg.params[0][1]), high: parseFloat(msg.params[0][3]), low: parseFloat(msg.params[0][4]), close: parseFloat(msg.params[0][2]) }) : null
  }
};


const CandleChart = ({ symbol, exchange = 'Binance', levels = [] }) => {
  const chartContainerRef = useRef();
  const seriesRef = useRef(null);
  const wsRef = useRef(null);
  const chartRef = useRef(null);
  const lastTimeRef = useRef(0);
  const reconnectCountRef = useRef(0);
  

  const priceLinesRef = useRef([]); 
  const [isLoading, setIsLoading] = useState(true);

  const getKucoinToken = async () => {
    try {
      const { data } = await api.post('api/proxy/kucoin-token/');
      return data.code === "200000" && data.data?.instanceServers?.[0]?.endpoint ? `${data.data.instanceServers[0].endpoint}?token=${data.data.token}` : null;
    } catch (e) { console.error('kucoin token error', e); return null; }
  };

  useEffect(() => {
    if (!seriesRef.current) return;

    priceLinesRef.current.forEach(line => {
      seriesRef.current.removePriceLine(line);
    });
    priceLinesRef.current = [];

    levels.forEach(lvl => {
      if (lvl.price && !isNaN(lvl.price) && parseFloat(lvl.price) > 0) {
        const line = seriesRef.current.createPriceLine({
          price: parseFloat(lvl.price),
          color: lvl.color || '#FFFFFF',
          lineWidth: 2,
          lineStyle: LineStyle.Dotted,
          axisLabelVisible: true,
          title: lvl.title || '',
        });
        priceLinesRef.current.push(line);
      }
    });
  }, [levels]); 

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: { background: { type: ColorType.Solid, color: '#000000' }, textColor: '#d1d4dc' },
      grid: { vertLines: { color: '#1f1f1f' }, horzLines: { color: '#1f1f1f' } },
      timeScale: { borderColor: '#333', timeVisible: true },
      height: 300,
    });
    chartRef.current = chart;

    const candlestickSeries = chart.addSeries(CandlestickSeries, { 
      upColor: '#26a69a', downColor: '#ef5350', wickUpColor: '#26a69a', wickDownColor: '#ef5350' 
    });
    seriesRef.current = candlestickSeries;

    let mounted = true;

    const connect = async () => {
      setIsLoading(true);
      reconnectCountRef.current = 0;
      const exCfg = CONFIG[exchange] || CONFIG.Binance;

      const doConnect = async () => {
        try {
          const res = await api.get('api/proxy/kline/', { params: { exchange, symbol, interval: '1m', limit: 150 } });
          let formatted = exCfg.parseHistory(res.data || []);
          formatted = (formatted || []).map(f => ({ ...f, time: normTime(f.time) })).sort((a,b)=>a.time-b.time);
          
          if (mounted && formatted.length) {
            seriesRef.current.setData(formatted);
            lastTimeRef.current = formatted[formatted.length - 1].time;
          }

          if (wsRef.current) {
            try { wsRef.current.close(); } catch (e) {}
            wsRef.current = null;
          }

          const wsUrl = await exCfg.getWsUrl(symbol, getKucoinToken);
          if (!wsUrl) { if(mounted) setIsLoading(false); return; }

          const ws = new WebSocket(wsUrl);
          wsRef.current = ws;

          ws.onopen = () => {
            if (exCfg.subscribe && ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify(exCfg.subscribe(symbol)));
            }
          };

          ws.onmessage = (event) => {
            let parsed;
            try { parsed = JSON.parse(event.data); } catch (e) { return; }
            const cand = exCfg.parseWS(parsed);
            if (cand) {
                cand.time = normTime(cand.time);
                if (cand.time >= lastTimeRef.current) {
                    seriesRef.current.update(cand);
                    lastTimeRef.current = cand.time;
                }
            }
          };

          ws.onclose = () => {
            if (reconnectCountRef.current < 3 && mounted) {
              reconnectCountRef.current += 1;
              setTimeout(() => { if (mounted) doConnect(); }, 1000 * reconnectCountRef.current);
            }
          };
        } catch (err) {
            console.error(err);
        } finally {
          if (mounted) setIsLoading(false);
        }
      }; 
      await doConnect();
    };

    connect();

    const handleResize = () => {
        if(chartContainerRef.current) {
            chart.applyOptions({ width: chartContainerRef.current.clientWidth });
        }
    }
    window.addEventListener('resize', handleResize);

    return () => {
      mounted = false;
      window.removeEventListener('resize', handleResize);
      if (wsRef.current) wsRef.current.close();
      chart.remove();
      priceLinesRef.current = [];
    };
  }, [symbol, exchange]); 

  return (
    <div className="bg-black rounded border border-secondary border-opacity-25" style={{ width: '100%', height: '300px', position: 'relative' }}>
      <div ref={chartContainerRef} style={{ width: '100%', height: '100%' }} />
      {isLoading && <div className="position-absolute top-0 start-0 p-2 text-secondary small">Loading...</div>}
    </div>
  );
};

export default CandleChart;