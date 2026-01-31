import React, { useContext, useState } from 'react';
import { TradeContext } from '../context/TradeContext'; 
import OrderBook from '../components/OrderBook';     
import CandleChart from '../components/CandleChart';
import api from '../api'; 

const DashboardPage = () => {
    const { longLeg, shortLeg } = useContext(TradeContext);
    
    const [amount, setAmount] = useState(100);
    const [longEntry, setLongEntry] = useState('');
    const [longExit, setLongExit] = useState('');
    const [shortEntry, setShortEntry] = useState('');
    const [shortExit, setShortExit] = useState('');

    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleExecute = async () => {
        if (!longLeg || !shortLeg) return;
        
        setIsSubmitting(true);

        const payload = {
            amount_usdt: parseFloat(amount),
            
            long_exchange: longLeg.exchange,
            long_symbol: longLeg.symbol,
            long_entry_target: longEntry ? parseFloat(longEntry) : null,
            long_exit_target: longExit ? parseFloat(longExit) : null,

            short_exchange: shortLeg.exchange,
            short_symbol: shortLeg.symbol,
            short_entry_target: shortEntry ? parseFloat(shortEntry) : null,
            short_exit_target: shortExit ? parseFloat(shortExit) : null
        };

        console.log("Sending Strategy:", payload);

        try {
            const response = await api.post('/positions/', payload);
            
            alert(`✅ Стратегия запущена!\nID: ${response.data.id}\nСтатус: ${response.data.status}`);
        } catch (error) {
            console.error("Execution error:", error);
            const errorMsg = error.response?.data 
                ? JSON.stringify(error.response.data, null, 2) 
                : "Ошибка соединения с сервером";
            alert(`❌ Ошибка создания позиции:\n${errorMsg}`);
        } finally {
            setIsSubmitting(false);
        }
    };

    const getLevels = (entry, exit, isLong) => {
        const levels = [];
        if (entry) levels.push({ 
            price: parseFloat(entry), 
            color: isLong ? '#00ff00' : '#ff0000', 
            title: 'ENTRY' 
        });
        if (exit) levels.push({ 
            price: parseFloat(exit), 
            color: isLong ? '#ff0000' : '#00ff00', 
            title: 'EXIT (TP)' 
        });
        return levels;
    };

    return (
        <div className="container-fluid py-3 min-vh-100 bg-black text-white">
            {/* Header */}
            <div className="d-flex justify-content-between align-items-center mb-3 px-2">
                <h4 className="text-white fw-bold m-0">
                    <i className="bi bi-cpu text-warning me-2"></i> 
                    Arbitrage Terminal
                </h4>
                {(!longLeg || !shortLeg) && (
                    <div className="alert alert-dark border-warning py-1 px-3 mb-0 text-warning small animate__animated animate__pulse animate__infinite">
                        <i className="bi bi-info-square-fill me-2"></i>
                        Выберите пары в таблице фандинга
                    </div>
                )}
            </div>

            <div className="row g-2 align-items-stretch">
                
                {/* === ЛЕВАЯ СТОРОНА (LONG) === */}
                <div className="col-lg-5">
                    <div className="h-100 p-2 border border-success border-opacity-25 bg-dark bg-opacity-10 rounded d-flex flex-column">
                        <div className="d-flex justify-content-between mb-2 px-1 align-items-center">
                            <div>
                                <span className="badge bg-success me-2">LONG</span>
                                <span className="text-white font-mono fw-bold">{longLeg ? `${longLeg.symbol}` : '--'}</span>
                                <span className="text-secondary small ms-2">{longLeg?.exchange}</span>
                            </div>
                        </div>
                        
                        {longLeg ? (
                            <div className="d-flex flex-column gap-2 flex-grow-1">
                                {/* Контролы цены для Long */}
                                <div className="d-flex gap-2">
                                    <div className="input-group input-group-sm">
                                        <span className="input-group-text bg-dark border-secondary text-success fw-bold">In</span>
                                        <input type="number" placeholder="Market" className="form-control bg-black text-white border-secondary" 
                                            value={longEntry} onChange={e => setLongEntry(e.target.value)} />
                                    </div>
                                    <div className="input-group input-group-sm">
                                        <span className="input-group-text bg-dark border-secondary text-danger fw-bold">Out</span>
                                        <input type="number" placeholder="Target" className="form-control bg-black text-white border-secondary" 
                                            value={longExit} onChange={e => setLongExit(e.target.value)} />
                                    </div>
                                </div>

                                <CandleChart 
                                    symbol={longLeg.symbol} 
                                    exchange={longLeg.exchange} 
                                    levels={getLevels(longEntry, longExit, true)}
                                />
                                <div className="flex-grow-1" style={{ minHeight: '300px' }}>
                                    <OrderBook symbol={longLeg.symbol} exchange={longLeg.exchange} />
                                </div>
                            </div>
                        ) : (
                            <EmptyState label="Ожидание Long пары..." />
                        )}
                    </div>
                </div>

                {/* === ЦЕНТРАЛЬНЫЙ БЛОК (EXECUTION) === */}
                <div className="col-lg-2 d-flex flex-column gap-2">
                    {/* Статус / Инфо */}
                    <div className="p-3 border border-secondary border-opacity-25 rounded bg-dark bg-opacity-10 text-center">
                        <small className="text-secondary d-block mb-1">Strategy</small>
                        <div className="fw-bold text-info">Funding Arb</div>
                    </div>

                    {/* Блок исполнения */}
                    <div className="p-3 border border-warning border-opacity-50 rounded bg-dark shadow-lg mt-auto">
                        <label className="text-secondary small mb-1 d-block text-center fw-bold">Size (USDT)</label>
                        <div className="input-group mb-3">
                            <span className="input-group-text bg-black border-secondary text-secondary">$</span>
                            <input 
                                type="number" 
                                className="form-control bg-black text-white border-secondary text-center fw-bold h6 mb-0" 
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                            />
                        </div>

                        <button 
                            className="btn btn-warning w-100 py-3 fw-bold shadow-warning"
                            disabled={!longLeg || !shortLeg || isSubmitting}
                            onClick={handleExecute}
                        >
                            {isSubmitting ? (
                                <>
                                    <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                                    Sending...
                                </>
                            ) : (
                                <>
                                    <i className="bi bi-lightning-fill me-1"></i> 
                                    EXECUTE
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {/* === ПРАВАЯ СТОРОНА (SHORT) === */}
                <div className="col-lg-5">
                    <div className="h-100 p-2 border border-danger border-opacity-25 bg-dark bg-opacity-10 rounded d-flex flex-column">
                        <div className="d-flex justify-content-between mb-2 px-1 align-items-center">
                            <div>
                                <span className="badge bg-danger me-2">SHORT</span>
                                <span className="text-white font-mono fw-bold">{shortLeg ? `${shortLeg.symbol}` : '--'}</span>
                                <span className="text-secondary small ms-2">{shortLeg?.exchange}</span>
                            </div>
                        </div>

                        {shortLeg ? (
                            <div className="d-flex flex-column gap-2 flex-grow-1">
                                {/* Контролы цены для Short */}
                                <div className="d-flex gap-2">
                                    <div className="input-group input-group-sm">
                                        <span className="input-group-text bg-dark border-secondary text-danger fw-bold">In</span>
                                        <input type="number" placeholder="Market" className="form-control bg-black text-white border-secondary" 
                                            value={shortEntry} onChange={e => setShortEntry(e.target.value)} />
                                    </div>
                                    <div className="input-group input-group-sm">
                                        <span className="input-group-text bg-dark border-secondary text-success fw-bold">Out</span>
                                        <input type="number" placeholder="Target" className="form-control bg-black text-white border-secondary" 
                                            value={shortExit} onChange={e => setShortExit(e.target.value)} />
                                    </div>
                                </div>

                                <CandleChart 
                                    symbol={shortLeg.symbol} 
                                    exchange={shortLeg.exchange}
                                    levels={getLevels(shortEntry, shortExit, false)}
                                />
                                <div className="flex-grow-1" style={{ minHeight: '300px' }}>
                                    <OrderBook symbol={shortLeg.symbol} exchange={shortLeg.exchange} />
                                </div>
                            </div>
                        ) : (
                            <EmptyState label="Ожидание Short пары..." />
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
};

const EmptyState = ({ label }) => (
    <div className="h-100 d-flex flex-column align-items-center justify-content-center text-secondary opacity-50">
        <div className="spinner-border mb-3" role="status" style={{width: '3rem', height: '3rem'}}></div>
        <span>{label}</span>
    </div>
);

export default DashboardPage;