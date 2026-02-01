import React, { useContext, useState, useEffect } from 'react'; 
import { TradeContext } from '../context/TradeContext';
import OrderBook from '../components/OrderBook';     
import CandleChart from '../components/CandleChart';
import api from '../api'; 
// 1. Импортируем toast
import { toast } from 'react-toastify'; 

const DashboardPage = () => {
    const { longLeg, shortLeg } = useContext(TradeContext);
    
    const [amount, setAmount] = useState(100);
    const [longEntry, setLongEntry] = useState('');
    const [longExit, setLongExit] = useState('');
    const [shortEntry, setShortEntry] = useState('');
    const [shortExit, setShortExit] = useState('');

    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        if (longLeg && longLeg.isExternalUpdate) {
            setLongEntry(longLeg.entryTarget || '');
            setLongExit(longLeg.exitTarget || '');
            if (longLeg.amount) setAmount(longLeg.amount);
        }
    }, [longLeg]);

    useEffect(() => {
        if (shortLeg && shortLeg.isExternalUpdate) {
            setShortEntry(shortLeg.entryTarget || '');
            setShortExit(shortLeg.exitTarget || '');
        }
    }, [shortLeg]);

    const handleExecute = async () => {
        if (!longLeg || !shortLeg) {
            toast.warn("Выберите обе ноги для стратегии", { theme: "dark" });
            return;
        }
        
        setIsSubmitting(true);

        const payload = {
            amount: parseFloat(amount),
            long_exchange: longLeg.exchange,
            long_symbol: longLeg.symbol,
            long_entry_target: longEntry ? parseFloat(longEntry) : null,
            long_exit_target: longExit ? parseFloat(longExit) : null,
            short_exchange: shortLeg.exchange,
            short_symbol: shortLeg.symbol,
            short_entry_target: shortEntry ? parseFloat(shortEntry) : null,
            short_exit_target: shortExit ? parseFloat(shortExit) : null
        };

        try {
            const response = await api.post('/positions/', payload);
            // 2. Успешное уведомление
            toast.success(
                <div>
                    <strong>✅ Стратегия запущена!</strong>
                    <div className="small opacity-75">ID: {response.data.id}</div>
                </div>, 
                { theme: "dark" }
            );
        } catch (error) {
            console.error("Execution error:", error);
            // 3. Уведомление об ошибке
            const errorMessage = error.response?.data 
                ? JSON.stringify(error.response.data) 
                : "Server error";
            toast.error(`❌ Ошибка: ${errorMessage}`, { theme: "dark" });
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
            </div>

            <div className="row g-2 align-items-stretch">
                {/* === LONG SIDE === */}
                <div className="col-lg-5">
                    <div className="h-100 p-2 border border-success border-opacity-25 bg-dark bg-opacity-10 rounded d-flex flex-column">
                        <div className="d-flex justify-content-between mb-2 px-1 align-items-center">
                            <div>
                                <span className="badge bg-success me-2">LONG</span>
                                <span className="text-white font-mono fw-bold">{longLeg ? longLeg.symbol : '--'}</span>
                                <span className="text-secondary small ms-2">{longLeg?.exchange}</span>
                            </div>
                        </div>
                        
                        {longLeg ? (
                            <div className="d-flex flex-column gap-2 flex-grow-1">
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
                        ) : <EmptyState label="Ожидание Long пары..." />}
                    </div>
                </div>

                {/* === EXECUTION === */}
                <div className="col-lg-2 d-flex flex-column gap-2">
                    <div className="p-3 border border-secondary border-opacity-25 rounded bg-dark bg-opacity-10 text-center">
                        <small className="text-secondary d-block mb-1">Strategy</small>
                        <div className="fw-bold text-info">Funding Arb</div>
                    </div>

                    <div className="p-3 border border-warning border-opacity-50 rounded bg-dark shadow-lg mt-auto">
                        <label className="text-secondary small mb-1 d-block text-center fw-bold">Size (Tokens)</label>
                        <div className="input-group mb-3">
                            <span className="input-group-text bg-black border-secondary text-secondary">#</span>
                            <input 
                                type="number" 
                                className="form-control bg-black text-white border-secondary text-center fw-bold" 
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
                                <span className="spinner-border spinner-border-sm me-2"></span>
                            ) : null}
                            {isSubmitting ? 'Sending...' : 'EXECUTE'}
                        </button>
                    </div>
                </div>

                {/* === SHORT SIDE === */}
                <div className="col-lg-5">
                    <div className="h-100 p-2 border border-danger border-opacity-25 bg-dark bg-opacity-10 rounded d-flex flex-column">
                        <div className="d-flex justify-content-between mb-2 px-1 align-items-center">
                            <div>
                                <span className="badge bg-danger me-2">SHORT</span>
                                <span className="text-white font-mono fw-bold">{shortLeg ? shortLeg.symbol : '--'}</span>
                                <span className="text-secondary small ms-2">{shortLeg?.exchange}</span>
                            </div>
                        </div>

                        {shortLeg ? (
                            <div className="d-flex flex-column gap-2 flex-grow-1">
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
                        ) : <EmptyState label="Ожидание Short пары..." />}
                    </div>
                </div>
            </div>
        </div>
    );
};

const EmptyState = ({ label }) => (
    <div className="h-100 d-flex flex-column align-items-center justify-content-center text-secondary opacity-50">
        <div className="spinner-border mb-3" role="status" style={{width: '2rem', height: '2rem'}}></div>
        <span>{label}</span>
    </div>
);

export default DashboardPage;