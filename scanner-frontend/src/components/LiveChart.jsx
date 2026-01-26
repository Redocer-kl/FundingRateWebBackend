import React, { useEffect, useState, useRef } from 'react';
import { AreaChart, Area, YAxis, XAxis, ResponsiveContainer, Tooltip } from 'recharts';

const LiveChart = ({ symbol, color = "#ffc107" }) => {
    const [data, setData] = useState([]);
    const ws = useRef(null);

    useEffect(() => {
        setData([]); // Сброс при смене монеты
        const pair = symbol.toLowerCase();
        
        // Подключаемся к потоку сделок (aggTrade) - это самые быстрые данные о цене
        ws.current = new WebSocket(`wss://fstream.binance.com/ws/${pair}@aggTrade`);

        ws.current.onmessage = (event) => {
            const message = JSON.parse(event.data);
            const price = parseFloat(message.p);
            const time = message.T;

            setData(prev => {
                // Оставляем только последние 50 точек, чтобы график "бежал" и не тормозил браузер
                const newData = [...prev, { time, price }];
                if (newData.length > 50) return newData.slice(newData.length - 50);
                return newData;
            });
        };

        return () => {
            if (ws.current) ws.current.close();
        };
    }, [symbol]);

    // Вычисляем мин/макс для масштабирования оси Y, чтобы график был "во весь рост"
    const minPrice = data.length > 0 ? Math.min(...data.map(d => d.price)) : 0;
    const maxPrice = data.length > 0 ? Math.max(...data.map(d => d.price)) : 0;
    // Добавляем маленький отступ сверху и снизу
    const domainMin = minPrice - (maxPrice - minPrice) * 0.1; 
    const domainMax = maxPrice + (maxPrice - minPrice) * 0.1;

    return (
        <div className="scanner-card p-3 border border-secondary mb-3" style={{ height: '250px' }}>
            <div className="d-flex justify-content-between align-items-center mb-2">
                <span className="fw-bold text-white small">LIVE PRICE ACTION</span>
                <span className="fw-bold fs-5" style={{ color: color }}>
                    {data.length > 0 ? data[data.length - 1].price.toFixed(2) : '...'}
                </span>
            </div>
            
            <div style={{ width: '100%', height: '100%' }}>
                <ResponsiveContainer>
                    <AreaChart data={data}>
                        <defs>
                            <linearGradient id={`grad${symbol}`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
                                <stop offset="95%" stopColor={color} stopOpacity={0}/>
                            </linearGradient>
                        </defs>
                        {/* Скрываем оси для чистоты, оставляем только линию */}
                        <XAxis dataKey="time" hide={true} />
                        <YAxis domain={[domainMin, domainMax]} hide={true} />
                        <Tooltip 
                            contentStyle={{ backgroundColor: '#111', borderColor: '#333' }}
                            itemStyle={{ color: '#fff' }}
                            formatter={(value) => [value, 'Price']}
                            labelFormatter={() => ''}
                        />
                        <Area 
                            type="monotone" 
                            dataKey="price" 
                            stroke={color} 
                            fillOpacity={1} 
                            fill={`url(#grad${symbol})`} 
                            isAnimationActive={false} 
                            strokeWidth={2}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default LiveChart;