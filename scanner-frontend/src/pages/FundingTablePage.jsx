import { useEffect, useState, useCallback, useContext } from 'react';
import { LineChart, Line, ResponsiveContainer, YAxis, ReferenceLine, CartesianGrid } from 'recharts';
import api from '../api';
import { Link } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { TradeContext } from '../context/TradeContext'; 
import { toast } from 'react-toastify'; 

const FundingTablePage = () => {
    const { user } = useContext(AuthContext);
    
    // Достаем методы для установки позиций
    const { setLongLeg, setShortLeg } = useContext(TradeContext);

    const navigate = useNavigate();
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [totalPages, setTotalPages] = useState(1);
    const [currentPage, setCurrentPage] = useState(1);
    const [favorites, setFavorites] = useState([]);
    
    const [searchTerm, setSearchTerm] = useState('');
    const [showFilterModal, setShowFilterModal] = useState(false);
    
    const [hoveredData, setHoveredData] = useState(null);
    const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

    const availableExchanges = ['Binance', 'Kucoin', 'Bitget', 'CoinEx', 'Paradex', 'Hyperliquid'];

    const [tempFilters, setTempFilters] = useState({
        period: localStorage.getItem('f_period') || '30d',
        sort: localStorage.getItem('f_sort') || 'spread',
        exchanges: JSON.parse(localStorage.getItem('f_exchanges')) || ['Binance', 'Bybit', 'OKX', 'Kucoin', 'Bitget']
    });

    const [appliedFilters, setAppliedFilters] = useState({...tempFilters});

    const sortOptions = [
        { label: 'Спред', value: 'spread' },
        { label: 'Макс. APR', value: 'apr' },
        { label: 'Market Cap', value: 'market_cap' },
        { label: 'Объем', value: 'volume' }
    ];

    const handleSelectPosition = (type, rawSymbol, exchange) => {
        const symbol = rawSymbol.toUpperCase().endsWith('USDT') 
            ? rawSymbol.toUpperCase() 
            : `${rawSymbol.toUpperCase()}USDT`;

        const positionData = { symbol, exchange };

        if (type === 'LONG') {
            setLongLeg(positionData);
            toast.success(`LONG: ${symbol} (${exchange}) выбран!`, { theme: "dark" });
        } else {
            setShortLeg(positionData);
            toast.error(`SHORT: ${symbol} (${exchange}) выбран!`, { theme: "dark" });
        }
    };

    const fetchFavorites = useCallback(async () => {
        const token = localStorage.getItem('access');
        if (token) {
            try {
                const res = await api.get('profile/');
                setFavorites(res.data.favorites.map(f => f.asset_symbol));
            } catch (err) { console.error("Ошибка загрузки избранного", err); }
        }
    }, []);

    const toggleFavorite = async (symbol) => {
        if (!user) {
            navigate('/login'); 
            return;
        }
        try {
            await api.post('favorite/toggle/', { asset_symbol: symbol });
            setFavorites(prev => 
                prev.includes(symbol) ? prev.filter(s => s !== symbol) : [...prev, symbol]
            );
        } catch (err) { console.error("Ошибка переключения избранного", err); }
    };

    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            params.append('page', currentPage);
            params.append('period', appliedFilters.period);
            params.append('sort', appliedFilters.sort);
            params.append('q', searchTerm);
            appliedFilters.exchanges.forEach(ex => params.append('exchanges', ex));

            const res = await api.get(`funding-table/?${params.toString()}`);
            setData(res.data.results || []);
            setTotalPages(res.data.total_pages || 1);
        } catch (err) { console.error(err); } finally { setLoading(false); }
    }, [currentPage, appliedFilters, searchTerm]);

    useEffect(() => {
        fetchData();
        fetchFavorites();
    }, [fetchData, fetchFavorites]);

    const handleApplyFilters = () => {
        setAppliedFilters({...tempFilters});
        setCurrentPage(1);
        setShowFilterModal(false);
        localStorage.setItem('f_period', tempFilters.period);
        localStorage.setItem('f_sort', tempFilters.sort);
        localStorage.setItem('f_exchanges', JSON.stringify(tempFilters.exchanges));
    };

    const handleMouseEnter = (e, row, symbol) => {
        const rect = e.currentTarget.getBoundingClientRect();
        setTooltipPos({ 
            x: rect.left > window.innerWidth / 2 ? rect.left - 360 : rect.left + 50, 
            y: rect.top - 120 
        });
        setHoveredData({
            history: row.history.map((v, i) => ({ i, v })),
            exchange: row.exchange,
            symbol: symbol,
            min: Math.min(...row.history),
            max: Math.max(...row.history)
        });
    };

    return (
        <div className="container-fluid py-3 text-white">
            <div className="scanner-card mb-3 p-3 bg-dark rounded border border-secondary">
                <div className="row g-3 align-items-center">
                    <div className="col-md-4">
                        <div className="input-group">
                            <span className="input-group-text bg-black border-secondary"><i className="bi bi-search text-warning"></i></span>
                            <input 
                                type="text" className="form-control bg-black border-secondary text-white shadow-none" 
                                placeholder="Поиск..." value={searchTerm} onChange={(e) => {setSearchTerm(e.target.value); setCurrentPage(1);}}
                            />
                        </div>
                    </div>
                    <div className="col-md-8 text-md-end">
                        <button className="btn btn-outline-warning" onClick={() => setShowFilterModal(true)}>
                            <i className="bi bi-sliders me-2"></i> Настройки
                        </button>
                    </div>
                </div>
            </div>

            <div className="scanner-card p-0 overflow-hidden shadow-lg border border-secondary rounded-3">
                <div className="table-responsive">
                    <table className="table table-dark table-hover mb-0">
                        <thead>
                            <tr className="small text-uppercase text-muted border-bottom border-secondary">
                                <th className="ps-4 py-3">Монета / Биржа</th>
                                <th className="text-end">Цена</th>
                                <th className="text-end">Avg APR</th>
                                <th className="text-center">Выплат</th>
                                {/* ДОБАВИЛ КОЛОНКУ TRADE */}
                                <th className="text-end pe-4">Trade</th>
                            </tr>
                        </thead>
                        {loading ? (
                            <tbody><tr><td colSpan="5" className="text-center py-5">Загрузка...</td></tr></tbody>
                        ) : (
                            data.map((item) => (
                                <tbody key={item.symbol} className="border-bottom border-secondary border-opacity-25">
                                    <tr style={{ backgroundColor: '#1a1a1a' }}>
                                        <td colSpan="5" className="px-3 py-2">
                                            <div className="d-flex align-items-center">
                                                <i className={`bi ${favorites.includes(item.symbol) ? 'bi-star-fill text-warning' : 'bi-star text-light'} cursor-pointer me-3 fs-5`} 
                                                   onClick={() => toggleFavorite(item.symbol)}></i>
                                                {item.asset_info?.image && (
                                                    <img src={item.asset_info.image} width="24" height="24" className="rounded-circle me-2" alt=""/>
                                                )}
                                                <Link to={`/coin/${item.symbol}`} className="text-decoration-none"><span className="fw-bold fs-5 me-4">{item.symbol}</span></Link>
                                                <div className="d-flex gap-4 opacity-75 small">
                                                    <span>MCap: <span className="text-warning">${(item.asset_info?.market_cap / 1e6).toFixed(1)}M</span></span>
                                                    <span>Vol: <span className="text-warning">${(item.asset_info?.volume / 1e6).toFixed(1)}M</span></span>
                                                </div>
                                                <span className="ms-auto badge bg-success bg-opacity-10 text-success border border-success border-opacity-25">
                                                    Spread: {item.spread.toFixed(2)}%
                                                </span>
                                            </div>
                                        </td>
                                    </tr>
                                    {item.exchanges_data.map((row, idx) => (
                                        <tr key={idx} className="align-middle border-0">
                                            <td className="ps-5 text-secondary py-2 small">
                                                <span className="opacity-25">└</span> {row.exchange}
                                            </td>
                                            <td className="text-end font-mono small">${row.price?.toLocaleString()}</td>
                                            <td 
                                                className={`text-end fw-bold px-3 ${row.hist_apr >= 0 ? 'text-success' : 'text-danger'}`}
                                                onMouseEnter={(e) => handleMouseEnter(e, row, item.symbol)}
                                                onMouseLeave={() => setHoveredData(null)}
                                                style={{ textDecoration: 'underline dotted', cursor: 'help' }}
                                            >
                                                {row.hist_apr?.toFixed(2)}%
                                            </td>
                                            <td className="text-center">
                                                <span className="badge bg-dark border border-secondary text-light">{row.frequency}x</span>
                                            </td>
                                            
                                            {/* === КНОПКИ LONG / SHORT === */}
                                            <td className="text-end pe-4">
                                                <div className="btn-group btn-group-sm">
                                                    <button 
                                                        className="btn btn-outline-success py-0 px-2 font-mono fw-bold" 
                                                        title="В Лонг"
                                                        onClick={() => handleSelectPosition('LONG', item.symbol, row.exchange)}
                                                    >L</button>
                                                    <button 
                                                        className="btn btn-outline-danger py-0 px-2 font-mono fw-bold" 
                                                        title="В Шорт"
                                                        onClick={() => handleSelectPosition('SHORT', item.symbol, row.exchange)}
                                                    >S</button>
                                                </div>
                                            </td>
                                            {/* =========================== */}

                                        </tr>
                                    ))}
                                </tbody>
                            ))
                        )}
                    </table>
                </div>

                {totalPages > 1 && (
                    <div className="d-flex flex-column flex-md-row justify-content-between align-items-center p-3 bg-black border-top border-secondary gap-3">
                        <span className="text-muted small">
                            Показано объектов: <span className="text-white">{data.length}</span> (Стр. {currentPage} из {totalPages})
                        </span>
                        
                        <nav>
                            <ul className="pagination pagination-sm mb-0 shadow-sm">
                                <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
                                    <button 
                                        className="page-link bg-dark border-secondary text-white px-3" 
                                        onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                                    >
                                        <i className="bi bi-chevron-left text-warning"></i>
                                    </button>
                                </li>

                                {(() => {
                                    let pages = [];
                                    const start = Math.max(1, currentPage - 2);
                                    const end = Math.min(totalPages, currentPage + 2);

                                    for (let i = start; i <= end; i++) {
                                        pages.push(
                                            <li key={i} className={`page-item ${currentPage === i ? 'active' : ''}`}>
                                                <button 
                                                    className={`page-link border-secondary ${currentPage === i ? 'bg-warning border-warning text-dark fw-bold' : 'bg-dark text-white'}`}
                                                    onClick={() => setCurrentPage(i)}
                                                >
                                                    {i}
                                                </button>
                                            </li>
                                        );
                                    }
                                    return pages;
                                })()}

                                <li className={`page-item ${currentPage === totalPages ? 'disabled' : ''}`}>
                                    <button 
                                        className="page-link bg-dark border-secondary text-white px-3" 
                                        onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                                    >
                                        <i className="bi bi-chevron-right text-warning"></i>
                                    </button>
                                </li>
                            </ul>
                        </nav>
                    </div>
                )}
            </div>

            {/* ГРАФИК */}
            {hoveredData && (
                <div 
                    className="position-fixed bg-dark border border-warning rounded-3 shadow-lg p-3"
                    style={{ left: tooltipPos.x, top: tooltipPos.y, width: '350px', height: '250px', zIndex: 10000, pointerEvents: 'none' }}
                >
                    <div className="d-flex justify-content-between small mb-2 border-bottom border-secondary pb-1">
                        <span className="fw-bold">{hoveredData.symbol} ({hoveredData.exchange})</span>
                        <span className="text-warning">Hist {appliedFilters.period}</span>
                    </div>
                    <div className="d-flex justify-content-between mb-1" style={{ fontSize: '11px' }}>
                        <span className="text-danger">Min: {hoveredData.min.toFixed(3)}%</span>
                        <span className="text-success">Max: {hoveredData.max.toFixed(3)}%</span>
                    </div>
                    <ResponsiveContainer width="100%" height="75%">
                        <LineChart data={hoveredData.history}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                            <YAxis hide domain={['auto', 'auto']} />
                            <ReferenceLine y={0} stroke="#666" strokeWidth={1} label={{ position: 'right', value: '0', fill: '#666', fontSize: 10 }} />
                            <Line type="monotone" dataKey="v" stroke="#ffc107" strokeWidth={2} dot={false} isAnimationActive={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* МОДАЛКА */}
            {showFilterModal && (
                <div className="filter-overlay" style={{ position: 'fixed', top:0, left:0, width:'100%', height:'100%', background:'rgba(0,0,0,0.8)', zIndex: 11000, display:'flex', alignItems:'center', justifyContent:'center' }}>
                    <div className="filter-content bg-dark border border-secondary p-4 rounded-3 shadow-lg" style={{ width: '450px' }}>
                        <h5 className="mb-4">Настройки скринера</h5>
                        
                        <div className="mb-4">
                            <label className="text-muted small d-block mb-2">Сортировка</label>
                            <select className="form-select bg-black text-white border-secondary shadow-none" value={tempFilters.sort} onChange={(e) => setTempFilters({...tempFilters, sort: e.target.value})}>
                                {sortOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                            </select>
                        </div>

                        <div className="mb-4">
                            <label className="text-muted small d-block mb-2">Период истории</label>
                            <div className="btn-group w-100">
                                {['1d', '3d', '7d', '14d', '30d'].map(p => (
                                    <button key={p} className={`btn btn-sm ${tempFilters.period === p ? 'btn-warning text-black' : 'btn-outline-secondary text-white'}`} onClick={() => setTempFilters({...tempFilters, period: p})}>{p}</button>
                                ))}
                            </div>
                        </div>

                        <div className="mb-4">
                            <label className="text-muted small d-block mb-2">Биржи</label>
                            <div className="row g-2 px-1" style={{ maxHeight: '160px', overflowY: 'auto' }}>
                                {availableExchanges.map(ex => (
                                    <div key={ex} className="col-6">
                                        <div className="form-check custom-check">
                                            <input 
                                                className="form-check-input shadow-none" 
                                                type="checkbox" 
                                                id={`ex-${ex}`}
                                                checked={tempFilters.exchanges.includes(ex)}
                                                onChange={() => {
                                                    const exs = tempFilters.exchanges.includes(ex) 
                                                        ? tempFilters.exchanges.filter(e => e !== ex) 
                                                        : [...tempFilters.exchanges, ex];
                                                    setTempFilters({...tempFilters, exchanges: exs});
                                                }}
                                            />
                                            <label className="form-check-label small cursor-pointer" htmlFor={`ex-${ex}`}>{ex}</label>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="d-flex gap-2 pt-2">
                            <button className="btn btn-warning fw-bold flex-grow-1" onClick={handleApplyFilters}>Обновить данные</button>
                            <button className="btn btn-outline-secondary text-white" onClick={() => setShowFilterModal(false)}>Отмена</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default FundingTablePage;