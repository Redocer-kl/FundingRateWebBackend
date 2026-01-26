import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';

const HomePage = () => {
    const [stats, setStats] = useState({
        total_coins: 0,
        total_exchanges: 0,
        last_update: null
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get('stats/')
            .then(res => {
                setStats(res.data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Ошибка загрузки статистики:", err);
                setLoading(false);
            });
    }, []);

    const formatDate = (dateString) => {
        if (!dateString) return '--:--';
        const date = new Date(dateString);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    return (
        <div className="container py-5 text-white">
            {/* Header */}
            <div className="text-center mb-5">
                <h1 className="display-4 fw-bold">
                    Funding <span className="text-warning">Scanner</span>
                </h1>
                {/* Заменил text-muted на более яркий для Lead текста */}
                <p className="lead" style={{ color: '#ced4da' }}>
                    Профессиональный инструмент для поиска арбитражных возможностей и анализа ставок финансирования.
                </p>
                
                {!loading && stats.last_update && (
                    <div className="badge bg-dark border border-secondary p-2 mt-2 shadow-sm">
                        <span className="text-success me-1">●</span> 
                        <span className="text-light">Последнее обновление: {formatDate(stats.last_update)} UTC</span>
                    </div>
                )}
            </div>

            {/* Stats Grid */}
            <div className="row g-4 mb-5 text-center">
                {[
                    { label: 'Монет в базе', value: stats.total_coins },
                    { label: 'Подключенных бирж', value: stats.total_exchanges },
                    { label: 'Глубина истории', value: '30 дней' }
                ].map((stat, idx) => (
                    <div className="col-md-4" key={idx}>
                        <div className="bg-dark p-4 rounded-3 border border-secondary h-100 shadow-sm">
                            <h3 className="text-warning fw-bold mb-0">{loading ? '...' : stat.value}</h3>
                            <span className="small text-uppercase tracking-wider" style={{ color: '#a0a0a0' }}>{stat.label}</span>
                        </div>
                    </div>
                ))}
            </div>

            {/* Navigation Cards */}
            <div className="row g-4">
                <div className="col-md-6">
                    <div className="card bg-dark border-secondary h-100 home-card shadow">
                        <div className="card-body p-4 d-flex flex-column">
                            <div className="mb-3 text-warning">
                                <i className="bi bi-grid-3x3-gap-fill fs-1"></i>
                            </div>
                            <h3 className="card-title text-white">Таблица Спредов</h3>
                            <p className="card-text mb-4" style={{ color: '#adb5bd' }}>
                                Полный список всех монет с расчетом разницы APR между биржами. Идеально для Delta-Neutral стратегий.
                            </p>
                            <Link to="/funding-table" className="btn btn-warning w-100 fw-bold py-2 mt-auto">Открыть таблицу</Link>
                        </div>
                    </div>
                </div>

                <div className="col-md-6">
                    <div className="card bg-dark border-secondary h-100 home-card shadow">
                        <div className="card-body p-4 d-flex flex-column">
                            <div className="mb-3 text-success">
                                <i className="bi bi-graph-up-arrow fs-1"></i>
                            </div>
                            <h3 className="card-title text-white">Лучшие связки</h3>
                            <p className="card-text mb-4" style={{ color: '#adb5bd' }}>
                                Топ самых высоких ставок по отдельным биржам. Найдите, где платят больше всего за лонг или шорт.
                            </p>
                            <Link to="/best-opportunities" className="btn btn-outline-success w-100 fw-bold py-2 mt-auto">Смотреть топ</Link>
                        </div>
                    </div>
                </div>
            </div>

            {/* How it works - Изменил фон на более контрастный */}
            <div className="mt-5 p-4 rounded-3 info-section">
                <h5 className="text-white mb-4 border-bottom border-secondary pb-2">Как это работает?</h5>
                <div className="row g-4">
                    {[
                        { step: '1. Сбор данных', text: 'Наш сканер каждые несколько часов опрашивает API Hyperliquid, Bitget и Paradex.' },
                        { step: '2. Анализ APR', text: 'Мы пересчитываем разовые выплаты в годовой процент (APR) для удобного сравнения.' },
                        { step: '3. Поиск спредов', text: 'Система находит разницу в ставках между биржами на одной и той же монете.' }
                    ].map((item, i) => (
                        <div className="col-md-4" key={i}>
                            <p className="mb-1 text-light fw-bold">{item.step}</p>
                            <p className="mb-0 small" style={{ color: '#b0b8c1' }}>{item.text}</p>
                        </div>
                    ))}
                </div>
            </div>

            <style>{`
                .home-card { transition: all 0.3s ease; }
                .home-card:hover {
                    transform: translateY(-5px);
                    border-color: #f0b90b !important;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.6) !important;
                }
                .tracking-wider { letter-spacing: 1px; }
            `}</style>
        </div>
    );
};

export default HomePage;