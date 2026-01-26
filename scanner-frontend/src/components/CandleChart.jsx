import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, CrosshairMode, CandlestickSeries } from 'lightweight-charts';
import axios from 'axios';

const CandleChart = ({ symbol }) => {
    const chartContainerRef = useRef();
    const chartRef = useRef(null); // Храним ссылку на инстанс графика
    const seriesRef = useRef(null); // Храним ссылку на серию данных
    const wsRef = useRef(null);
    const [isLoading, setIsLoading] = useState(true);

    // Функция для форматирования данных от Binance в формат Lightweight Charts
    const formatCandle = (kline) => ({
        time: kline[0] / 1000, // Binance дает мс, LW Charts хочет секунды
        open: parseFloat(kline[1]),
        high: parseFloat(kline[2]),
        low: parseFloat(kline[3]),
        close: parseFloat(kline[4]),
    });

    useEffect(() => {
        if (!chartContainerRef.current) return;

        // 1. ИНИЦИАЛИЗАЦИЯ ГРАФИКА
        // Настраиваем темную тему
        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: '#1a1a1a' },
                textColor: '#d1d4dc',
            },
            grid: {
                vertLines: { color: 'rgba(42, 46, 57, 0.2)' },
                horzLines: { color: 'rgba(42, 46, 57, 0.2)' },
            },
            crosshair: {
                mode: CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: 'rgba(197, 203, 206, 0.1)',
            },
            timeScale: {
                borderColor: 'rgba(197, 203, 206, 0.1)',
                timeVisible: true,
                secondsVisible: false,
            },
            height: 300, // Высота контейнера
        });

        chartRef.current = chart;

        // Добавляем серию свечей с классическими цветами
        const candlestickSeries = chart.addSeries(CandlestickSeries, {
            upColor: '#00e676',
            downColor: '#ff5252',
            borderVisible: false,
            wickUpColor: '#00e676',
            wickDownColor: '#ff5252',
        });
        seriesRef.current = candlestickSeries;

        // Адаптация под размер окна
        const handleResize = () => {
            chart.applyOptions({ width: chartContainerRef.current.clientWidth });
        };
        window.addEventListener('resize', handleResize);


        // 2. ЗАГРУЗКА ИСТОРИИ И ПОДКЛЮЧЕНИЕ WS
        const loadData = async () => {
            setIsLoading(true);
            const pair = symbol.toUpperCase(); // Для REST API нужен верхний регистр

            try {
                // Запрашиваем последние 100 свечей по 1 минуте (1m)
                const res = await axios.get(`https://fapi.binance.com/fapi/v1/klines?symbol=${pair}&interval=1m&limit=100`);
                const historicalData = res.data.map(formatCandle);
                candlestickSeries.setData(historicalData);
                
                // Центрируем график на последних данных
                chart.timeScale().fitContent();
                setIsLoading(false);

                // --- ПОДКЛЮЧАЕМ WEBSOCKET (только после загрузки истории) ---
                const wsPair = symbol.toLowerCase();
                wsRef.current = new WebSocket(`wss://fstream.binance.com/ws/${wsPair}@kline_1m`);

                wsRef.current.onmessage = (event) => {
                    const message = JSON.parse(event.data);
                    const k = message.k; // Данные свечи находятся в объекте 'k'

                    // Обновляем последнюю свечу в реальном времени
                    // Метод .update() сам решит: изменить текущую свечу или начать новую
                    candlestickSeries.update({
                        time: k.t / 1000,
                        open: parseFloat(k.o),
                        high: parseFloat(k.h),
                        low: parseFloat(k.l),
                        close: parseFloat(k.c),
                    });
                };

            } catch (err) {
                console.error("Ошибка загрузки данных графика:", err);
                setIsLoading(false);
            }
        };

        loadData();

        // CLEANUP при размонтировании или смене символа
        return () => {
            window.removeEventListener('resize', handleResize);
            if (wsRef.current) wsRef.current.close();
            chart.remove();
        };
    }, [symbol]);

    return (
        <div className="scanner-card p-0 border border-secondary mb-3 position-relative">
             {/* Заголовок */}
             <div className="p-2 border-bottom border-secondary bg-dark d-flex justify-content-between align-items-center small">
                <span className="fw-bold text-white">{symbol} / 1m Candles</span>
                <span className="badge bg-secondary text-light opacity-50">TradingView</span>
            </div>
            
            {/* Контейнер для графика */}
            <div ref={chartContainerRef} style={{ width: '100%', height: '300px' }} />

            {/* Спиннер загрузки */}
            {isLoading && (
                <div className="position-absolute top-50 start-50 translate-middle">
                    <div className="spinner-border text-warning" role="status"></div>
                </div>
            )}
        </div>
    );
};

export default CandleChart;