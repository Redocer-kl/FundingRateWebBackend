import React, { useEffect, useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import api from '../api';

// Цвета бирж настраиваем здесь
const EXCHANGE_COLORS = {
    'Hyperliquid': '#00ffa3',
    'Bitget': '#00f0ff',
    'Paradex': '#f0350b',
    'Binance': '#F3BA2F',
    'CoinEx': '#45fd24',
    'Kucoin': '#f73b9c'
};

const CoinDetailPage = () => {
    const { symbol } = useParams();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get(`coin-detail/${symbol}/`)
            .then(res => {
                setData(res.data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Ошибка загрузки:", err);
                setLoading(false);
            });
    }, [symbol]);

    // Форматируем историю для графика Recharts
    const formattedChartData = useMemo(() => {
        if (!data || !data.history) return [];
        const timeMap = {};
        data.history.forEach(ex => {
            ex.points.forEach(p => {
                const ts = new Date(p.t).getTime();
                if (!timeMap[ts]) timeMap[ts] = { time: ts };
                timeMap[ts][ex.exchange] = parseFloat(p.v.toFixed(4));
            });
        });
        return Object.values(timeMap).sort((a, b) => a.time - b.time);
    }, [data]);

    if (loading) return <div className="p-5 text-center text-muted">Загрузка данных {symbol}...</div>;
    if (!data) return <div className="p-5 text-center text-danger">Актив не найден</div>;

    return (
        <div className="container py-4">
            {/* Header */}
            <div className="scanner-card p-4 mb-4 shadow-sm border border-secondary">
                <div className="d-flex justify-content-between align-items-center">
                    <div className="d-flex align-items-center">
                        {data.asset?.image_url && (
                            <img src={data.asset.image_url} alt={symbol} width="52" height="52" className="rounded-circle me-3 border border-secondary shadow-sm" />
                        )}
                        <div>
                            <h2 className="mb-0 fw-bold text-white">{symbol}</h2>
                            <div className="d-flex gap-3 mt-1 small" style={{ color: '#adb5bd' }}>
                                {data.asset ? (
                                    <>
                                        <span>M.Cap: <b className="text-light">${(data.asset.market_cap / 1e6).toFixed(1)}M</b></span>
                                        <span>Vol 24h: <b className="text-light">${(data.asset.volume_24h / 1e6).toFixed(1)}M</b></span>
                                    </>
                                ) : (
                                    <span>Данные рынка отсутствуют</span>
                                )}
                            </div>
                        </div>
                    </div>
                    <Link to="/funding-table" className="btn btn-outline-secondary btn-sm px-3">
                        <i className="bi bi-arrow-left me-2"></i> К таблице
                    </Link>
                </div>
            </div>

            {/* Stats Widgets */}
            <div className="row g-3 mb-4">
                {data.summary_stats.map((stat, idx) => (
                    <div className="col-md-4" key={idx}>
                        <div className="p-3 rounded-3 h-100 border-start border-4" 
                             style={{ background: '#1e2329', borderColor: EXCHANGE_COLORS[stat.exchange] || '#666' }}>
                            <div className="d-flex justify-content-between align-items-center mb-3">
                                <h5 className="mb-0 fw-bold" style={{ color: EXCHANGE_COLORS[stat.exchange] || '#fff' }}>
                                    {stat.exchange}
                                </h5>
                                <span className="badge bg-dark border border-secondary text-muted">
                                    {stat.price?.toFixed(4)} $
                                </span>
                            </div>
                            <div className="row g-0">
                                <div className="col-6">
                                    <small className="text-muted d-block mb-1">Текущий APR</small>
                                    <span className={`fs-5 fw-bold ${stat.current_apr > 0 ? 'text-pos' : 'text-neg'}`}>
                                        {stat.current_apr.toFixed(2)}%
                                    </span>
                                </div>
                                <div className="col-6 text-end">
                                    <small className="text-muted d-block mb-1">Средний (30д)</small>
                                    <span className="fs-5 fw-bold text-white">{stat.avg_apr.toFixed(2)}%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Chart Area */}
            <div className="scanner-card p-4">
                <div className="d-flex justify-content-between align-items-center mb-4">
                    <h5 className="text-white mb-0">История APR (30 дней)</h5>
                    <small className="text-muted">Интервал: 1 час</small>
                </div>
                
                <div style={{ height: '450px', width: '100%', background: '#1e2329', borderRadius: '8px', padding: '10px' }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={formattedChartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#2a2e39" vertical={false} />
                            <XAxis 
                                dataKey="time" 
                                type="number" 
                                domain={['auto', 'auto']}
                                tickFormatter={(t) => new Date(t).toLocaleDateString()}
                                stroke="#848e9c" fontSize={12}
                            />
                            <YAxis orientation="right" stroke="#848e9c" fontSize={12} tickFormatter={(v) => `${v}%`} />
                            <Tooltip 
                                contentStyle={{ backgroundColor: '#1e2329', border: '1px solid #474d57', borderRadius: '8px' }}
                                labelStyle={{ color: '#f0b90b' }}
                                labelFormatter={(t) => new Date(t).toLocaleString()}
                            />
                            <Legend />
                            {data.history.map(ex => (
                                <Line 
                                    key={ex.exchange}
                                    type="monotone"
                                    dataKey={ex.exchange}
                                    stroke={EXCHANGE_COLORS[ex.exchange] || '#666'}
                                    dot={false}
                                    strokeWidth={2}
                                    connectNulls={true} 
                                />
                            ))}
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default CoinDetailPage;