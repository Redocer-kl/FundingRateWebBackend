import React, { useContext, useState } from 'react';
import { TradeContext } from '../context/TradeContext';
import OrderBook from '../components/OrderBook';
import CandleChart from '../components/CandleChart';
import { Link } from 'react-router-dom';

const DashboardPage = () => {
    const { longLeg, shortLeg } = useContext(TradeContext);
    const [amount, setAmount] = useState(100);

    const handleExecute = () => {
        if (!longLeg || !shortLeg) return;
        alert(`Сделка отправлена!\nLONG: ${longLeg.symbol}\nSHORT: ${shortLeg.symbol}\nСумма: $${amount}`);
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
                    <div className="h-100 p-2 border border-success border-opacity-25 bg-dark bg-opacity-10 rounded">
                        <div className="d-flex justify-content-between mb-2 px-1">
                            <span className="text-success fw-bold small">BUY / LONG</span>
                            <span className="text-secondary font-mono small">{longLeg ? `${longLeg.symbol} @ ${longLeg.exchange}` : '--'}</span>
                        </div>
                        
                        {longLeg ? (
                            <div className="d-flex flex-column gap-2">
                                <CandleChart symbol={longLeg.symbol} exchange={longLeg.exchange} />
                                <div style={{ height: '420px' }}>
                                    <OrderBook symbol={longLeg.symbol} exchange={longLeg.exchange} />
                                </div>
                            </div>
                        ) : (
                            <EmptyState label="Ожидание Long пары..." height="700px" />
                        )}
                    </div>
                </div>

                {/* === ЦЕНТРАЛЬНЫЙ БЛОК УПРАВЛЕНИЯ === */}
                <div className="col-lg-2 d-flex flex-column">
                    {/* Верхняя часть центра (инфо-панель) */}
                    <div className="flex-grow-1 p-3 border border-secondary border-opacity-25 rounded mb-2 bg-dark bg-opacity-10 d-flex flex-column align-items-center justify-content-center text-center">
                        <div className="text-secondary" style={{fontSize: '10px'}}>Market Neutral Strategy</div>
                    </div>

                    {/* НИЖНЯЯ ЧАСТЬ (EXECUTION) - Опущена к стаканам */}
                    <div className="p-3 border border-warning border-opacity-50 rounded bg-dark shadow-lg">
                        <div className="mb-3">
                            <label className="text-secondary small mb-2 d-block text-center fw-bold">Сумма (USDT)</label>
                            <div className="input-group">
                                <span className="input-group-text bg-black border-secondary text-secondary">$</span>
                                <input 
                                    type="number" 
                                    className="form-control bg-black text-white border-secondary text-center fw-bold h6 mb-0" 
                                    value={amount}
                                    onChange={(e) => setAmount(e.target.value)}
                                />
                            </div>
                        </div>

                        <button 
                            className="btn btn-warning w-100 py-3 fw-bold shadow-warning position-relative overflow-hidden"
                            disabled={!longLeg || !shortLeg}
                            onClick={handleExecute}
                        >
                            <i className="bi bi-lightning-fill me-1"></i> 
                            Открыть
                        </button>
                        

                    </div>
                </div>

                {/* === ПРАВАЯ СТОРОНА (SHORT) === */}
                <div className="col-lg-5">
                    <div className="h-100 p-2 border border-danger border-opacity-25 bg-dark bg-opacity-10 rounded">
                        <div className="d-flex justify-content-between mb-2 px-1">
                            <span className="text-secondary font-mono small">{shortLeg ? `${shortLeg.symbol} @ ${shortLeg.exchange}` : '--'}</span>
                            <span className="text-danger fw-bold small">SELL / SHORT</span>
                        </div>

                        {shortLeg ? (
                            <div className="d-flex flex-column gap-2">
                                <CandleChart symbol={shortLeg.symbol} exchange={shortLeg.exchange} />
                                <div style={{ height: '420px' }}>
                                    <OrderBook symbol={shortLeg.symbol} exchange={shortLeg.exchange} />
                                </div>
                            </div>
                        ) : (
                            <EmptyState label="Ожидание Short пары..." height="700px" />
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
};


const EmptyState = ({ label, height }) => (
    <div className="border border-secondary border-dashed rounded d-flex flex-column align-items-center justify-content-center text-secondary" style={{ height }}>
        <div className="spinner-grow text-secondary opacity-25 mb-3" role="status"></div>
        <span className="small">{label}</span>
    </div>
);

export default DashboardPage;