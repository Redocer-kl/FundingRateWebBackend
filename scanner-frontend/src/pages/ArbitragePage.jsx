import React, { useState } from 'react';
import OrderBook from '../components/OrderBook';
// Заменяем импорт
import CandleChart from '../components/CandleChart'; 

const ArbitragePage = () => {
    const [leftSymbol, setLeftSymbol] = useState('BTCUSDT');
    const [rightSymbol, setRightSymbol] = useState('ETHUSDT');
    
    const [inputLeft, setInputLeft] = useState('BTCUSDT');
    const [inputRight, setInputRight] = useState('ETHUSDT');

    return (
        <div className="container-fluid py-4">
            <h2 className="text-white mb-4 ps-2 border-start border-4 border-warning">
                Арбитражный терминал (Live)
            </h2>

            <div className="row g-4">
                {/* ЛЕВАЯ ПАНЕЛЬ */}
                <div className="col-lg-6">
                    <div className="mb-3 input-group">
                         <span className="input-group-text bg-dark border-secondary text-light">Symbol A</span>
                         <input 
                            type="text" 
                            className="form-control bg-dark text-white border-secondary"
                            value={inputLeft}
                            onChange={(e) => setInputLeft(e.target.value.toUpperCase())}
                         />
                         <button className="btn btn-warning fw-bold" onClick={() => setLeftSymbol(inputLeft)}>
                            Load
                         </button>
                    </div>

                    {/* Новые свечные графики */}
                    <CandleChart symbol={leftSymbol} />
                    
                    <div style={{height: '500px'}}>
                        <OrderBook symbol={leftSymbol} title={`LONG / ${leftSymbol}`} />
                    </div>
                </div>

                {/* ПРАВАЯ ПАНЕЛЬ */}
                <div className="col-lg-6">
                     <div className="mb-3 input-group">
                         <span className="input-group-text bg-dark border-secondary text-light">Symbol B</span>
                         <input 
                            type="text" 
                            className="form-control bg-dark text-white border-secondary"
                            value={inputRight}
                            onChange={(e) => setInputRight(e.target.value.toUpperCase())}
                         />
                         <button className="btn btn-info fw-bold" onClick={() => setRightSymbol(inputRight)}>
                            Load
                         </button>
                    </div>

                    {/* Новые свечные графики */}
                    <CandleChart symbol={rightSymbol} />

                    <div style={{height: '500px'}}>
                        <OrderBook symbol={rightSymbol} title={`SHORT / ${rightSymbol}`} />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ArbitragePage;