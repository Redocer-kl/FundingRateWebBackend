import React, { useState, useEffect, useCallback, useContext } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { TradeContext } from '../context/TradeContext'; 
import { toast } from 'react-toastify';

const BestOpportunitiesPage = () => {
    const { setLongLeg, setShortLeg } = useContext(TradeContext);

    const [opps, setOpps] = useState([]);
    const [loading, setLoading] = useState(true);
    const [pagination, setPagination] = useState({
        current_page: 1,
        total_pages: 1,
        count: 0
    });

    const [filters, setFilters] = useState({
        period: '1d',
        side: 'LONG', 
        q: ''
    });

    const loadData = useCallback(async (page = 1) => {
        setLoading(true);
        try {
            const params = {
                ...filters,
                page: page,
                page_size: 12 
            };
            const res = await api.get('api/best-opportunities/', { params });
            
            setOpps(res.data.results);
            setPagination({
                current_page: res.data.current_page,
                total_pages: res.data.total_pages,
                count: res.data.count
            });
        } catch (err) {
            console.error("Ошибка при загрузке связок:", err);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    useEffect(() => {
        loadData(1);
    }, [loadData]);

    const handleSelectPosition = (type, rawSymbol, exchange) => {
        const symbol = rawSymbol.toUpperCase().endsWith('USDT') 
            ? rawSymbol.toUpperCase() 
            : `${rawSymbol.toUpperCase()}USDT`;

        const positionData = { symbol, exchange };

        if (type === 'LONG') {
            setLongLeg(positionData);
            toast.success(`LONG: ${symbol} (${exchange}) добавлен в терминал`, { theme: "dark", autoClose: 2000 });
        } else {
            setShortLeg(positionData);
            toast.error(`SHORT: ${symbol} (${exchange}) добавлен в терминал`, { theme: "dark", autoClose: 2000 });
        }
    };

    const handleSearch = (e) => {
        e.preventDefault();
        loadData(1);
    };

    const renderPagination = () => {
        const { current_page, total_pages } = pagination;
        if (total_pages <= 1) return null;

        let pages = [];
        for (let i = Math.max(1, current_page - 2); i <= Math.min(total_pages, current_page + 2); i++) {
            pages.push(i);
        }

        return (
            <nav className="mt-5">
                <ul className="pagination justify-content-center">
                    <li className={`page-item ${current_page === 1 ? 'disabled' : ''}`}>
                        <button className="page-link bg-dark border-secondary text-white" onClick={() => loadData(current_page - 1)}>«</button>
                    </li>
                    {pages.map(num => (
                        <li key={num} className={`page-item ${current_page === num ? 'active' : ''}`}>
                            <button 
                                className={`page-link ${current_page === num ? 'bg-warning border-warning text-dark' : 'bg-dark border-secondary text-white'}`}
                                onClick={() => loadData(num)}
                            >
                                {num}
                            </button>
                        </li>
                    ))}
                    <li className={`page-item ${current_page === total_pages ? 'disabled' : ''}`}>
                        <button className="page-link bg-dark border-secondary text-white" onClick={() => loadData(current_page + 1)}>»</button>
                    </li>
                </ul>
            </nav>
        );
    };

    return (
        <div className="container py-4">
            {/* Хедер и Фильтры */}
            <div className="scanner-card p-4 mb-4 shadow-sm border border-secondary" style={{ backgroundColor: '#1a1a1a', borderRadius: '12px' }}>
                <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center mb-4 gap-3">
                    <h4 className="text-white mb-0">
                        <i className="bi bi-fire text-warning me-2"></i> Лучшие связки
                    </h4>
                    <form onSubmit={handleSearch} className="d-flex gap-2">
                        <input 
                            type="text" 
                            className="form-control form-control-sm bg-dark text-white border-secondary shadow-none"
                            placeholder="Поиск монеты..."
                            value={filters.q}
                            onChange={(e) => setFilters({...filters, q: e.target.value})}
                            style={{ width: '200px' }}
                        />
                        <button type="submit" className="btn btn-sm btn-warning fw-bold px-3">Найти</button>
                    </form>
                </div>

                <div className="row g-3">
                    <div className="col-md-6">
                        <label className="text-muted small d-block mb-2 text-uppercase fw-bold">Период расчета:</label>
                        <div className="btn-group shadow-sm">
                            {['1d', '3d', '7d', '14d', '30d'].map(p => (
                                <button 
                                    key={p}
                                    className={`btn btn-sm px-3 ${filters.period === p ? 'btn-warning active' : 'btn-outline-secondary text-white'}`}
                                    onClick={() => setFilters({...filters, period: p})}
                                >
                                    {p}
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className="col-md-6 text-md-end text-start">
                        <label className="text-muted small d-block mb-2 text-uppercase fw-bold">Направление APR:</label>
                        <div className="btn-group shadow-sm">
                            {/* УБРАЛИ ALL */}
                            {['LONG', 'SHORT'].map(s => (
                                <button 
                                    key={s}
                                    className={`btn btn-sm px-4 ${filters.side === s ? (s === 'LONG' ? 'btn-success' : 'btn-danger') : 'btn-outline-secondary text-white'}`}
                                    onClick={() => setFilters({...filters, side: s})}
                                >
                                    {s === 'LONG' ? 'Positive (Long)' : 'Negative (Short)'}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Сетка карточек */}
            {loading ? (
                <div className="text-center p-5">
                    <div className="spinner-border text-warning" role="status"></div>
                    <p className="text-muted mt-3">Анализируем рынок...</p>
                </div>
            ) : (
                <>
                    <div className="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
                        {opps.length > 0 ? opps.map((opp, idx) => (
                            <div className="col" key={`${opp.symbol}-${opp.exchange}-${idx}`}>
                                <div className="card h-100 bg-dark border-secondary shadow-sm" style={{ borderRadius: '15px', overflow: 'hidden' }}>
                                    <div className="card-body p-4">
                                        <div className="d-flex justify-content-between align-items-start mb-3">
                                            <div>
                                                <Link to={`/coin/${opp.symbol}`} className="text-decoration-none">
                                                    <h4 className="text-white fw-bold mb-0 hover-warning">{opp.symbol}</h4>
                                                </Link>
                                                <span className="badge bg-secondary-subtle text-secondary small mt-1">{opp.exchange}</span>
                                            </div>
                                            <span className={`badge ${opp.side === 'LONG' ? 'bg-success' : 'bg-danger'} px-3 py-2`}>
                                                {opp.side}
                                            </span>
                                        </div>
                                        
                                        <div className="bg-black bg-opacity-40 p-3 rounded-3 d-flex justify-content-between align-items-center border border-secondary border-opacity-25">
                                            <div>
                                                <div className="text-muted small mb-1" style={{ fontSize: '0.75rem' }}>AVG APR</div>
                                                <div className={`h3 mb-0 fw-bold ${opp.side === 'LONG' ? 'text-success' : 'text-danger'}`}>
                                                    {opp.apr}%
                                                </div>
                                            </div>
                                            <div className="text-end">
                                                <div className="text-muted small mb-1" style={{ fontSize: '0.75rem' }}>Price</div>
                                                <div className="text-white fw-bold">${opp.price > 1 ? opp.price.toLocaleString() : opp.price.toFixed(6)}</div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* УПРАВЛЕНИЕ: КНОПКИ ДЛЯ ТЕРМИНАЛА */}
                                    <div className="card-footer border-secondary bg-transparent p-3 d-flex gap-2">
                                        <button 
                                            className="btn btn-sm btn-outline-success flex-grow-1 fw-bold py-2"
                                            onClick={() => handleSelectPosition('LONG', opp.symbol, opp.exchange)}
                                        >
                                            + LONG
                                        </button>
                                        <button 
                                            className="btn btn-sm btn-outline-danger flex-grow-1 fw-bold py-2"
                                            onClick={() => handleSelectPosition('SHORT', opp.symbol, opp.exchange)}
                                        >
                                            + SHORT
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ) ) : (
                            <div className="col-12 text-center py-5">
                                <h5 className="text-muted">Ничего не найдено</h5>
                            </div>
                        )}
                    </div>
                    {renderPagination()}
                </>
            )}
        </div>
    );
};

export default BestOpportunitiesPage;