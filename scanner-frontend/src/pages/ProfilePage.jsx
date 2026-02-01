import React, { useEffect, useState, useContext } from 'react';
import api from '../api';
import { AuthContext } from '../context/AuthContext';
import { TradeContext } from '../context/TradeContext'; 
import { Link, useNavigate } from 'react-router-dom';

const ProfilePage = () => {
    const [profile, setProfile] = useState(null);
    const { logout } = useContext(AuthContext);
    const { setTradeParams } = useContext(TradeContext); 
    const navigate = useNavigate();

    const fetchProfile = () => {
        api.get('profile/')
            .then(res => setProfile(res.data))
            .catch(err => console.error(err));
    };

    useEffect(() => {
        fetchProfile();
    }, []);

    const renderStatusBadge = (status) => {
        const styles = {
            'OPEN': 'bg-success text-white',
            'PENDING': 'bg-warning text-dark',
            'CLOSED': 'bg-secondary text-light'
        };
        return <span className={`badge ${styles[status] || 'bg-dark'} extra-small-badge`} style={{fontSize: '10px'}}>{status}</span>;
    };

    const handleOpenInDashboard = (pos) => {
        setTradeParams({
            longExchange: pos.long_ticker.exchange,
            shortExchange: pos.short_ticker.exchange,
            symbol: pos.long_ticker.symbol,
            amount: pos.amount,
            longEntry: pos.long_entry_target,
            shortEntry: pos.short_entry_target,
            longExit: pos.long_exit_target,
            shortExit: pos.short_exit_target
        });
        navigate('/dashboard'); 
    };

    const handleClosePosition = async (id) => {
        if (window.confirm("Вы уверены, что хотите закрыть эту позицию?")) {
            try {
                await api.post(`positions/${id}/close/`);
                fetchProfile(); 
            } catch (err) {
                console.error("Ошибка при закрытии:", err);
                alert("Не удалось закрыть позицию");
            }
        }
    };

    if (!profile) return (
        <div className="d-flex justify-content-center align-items-center" style={{minHeight: '50vh'}}>
            <div className="spinner-border text-warning" role="status"></div>
            <span className="ms-3 text-light">Загрузка профиля...</span>
        </div>
    );

    return (
        <div className="container py-5">
            <div className="row g-4">
                {/* Левая колонка */}
                <div className="col-lg-3">
                    <div className="scanner-card p-4 border border-secondary shadow-lg mb-4">
                        <div className="text-center mb-4">
                            <div className="profile-avatar mx-auto mb-3">
                                <i className="bi bi-person-circle text-warning fs-1"></i>
                            </div>
                            <h4 className="text-white fw-bold mb-1">{profile.username}</h4>
                            <p className="custom-muted small mb-0">{profile.email}</p>
                        </div>
                        <button onClick={logout} className="btn btn-outline-danger w-100 btn-sm fw-bold">
                            ВЫЙТИ
                        </button>
                    </div>

                    <div className="scanner-card p-4 border border-secondary shadow-lg">
                        <h6 className="text-white mb-3 fw-bold small">ИЗБРАННОЕ</h6>
                        {profile.favorites?.map(fav => (
                            <div key={fav.id} className="d-flex justify-content-between align-items-center mb-2 p-2 border border-secondary rounded favorite-item">
                                <span className="text-warning fw-bold small">{fav.asset_symbol}</span>
                                <Link to={`/coin/${fav.asset_symbol}`} className="btn btn-sm btn-link text-warning p-0">
                                    <i className="bi bi-arrow-right-circle-fill"></i>
                                </Link>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Правая колонка: Все позиции */}
                <div className="col-lg-9">
                    <div className="scanner-card p-4 border border-secondary shadow-lg">
                        <h5 className="text-white mb-4 d-flex align-items-center fw-bold">
                            <i className="bi bi-activity text-warning me-2"></i> 
                            ЖУРНАЛ ТОРГОВЛИ
                        </h5>
                        
                        <div className="table-responsive">
                            <table className="table table-dark table-hover align-middle border-secondary">
                                <thead className="text-muted small">
                                    <tr style={{fontSize: '11px'}}>
                                        <th>ID / ТИКЕР</th>
                                        <th>БИРЖИ (L/S)</th>
                                        <th>СТАТУС</th>
                                        <th>ОБЪЕМ</th>
                                        <th>ЦЕЛИ (IN / OUT)</th>
                                        <th className="text-end">ДЕЙСТВИЕ</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {profile.positions && profile.positions.length > 0 ? (
                                        profile.positions.map(pos => (
                                            <tr key={pos.id} className={pos.status === 'CLOSED' ? 'opacity-50' : ''}>
                                                <td>
                                                    <div className="d-flex flex-column">
                                                        <span className="fw-bold text-white small">#{pos.id}</span>
                                                        <span className="text-warning font-mono" style={{fontSize: '12px'}}>
                                                            {pos.long_ticker.symbol}
                                                        </span>
                                                    </div>
                                                </td>
                                                <td>
                                                    <div className="d-flex flex-column small">
                                                        <span className="text-pos">{pos.long_ticker.exchange}</span>
                                                        <span className="text-neg">{pos.short_ticker.exchange}</span>
                                                    </div>
                                                </td>
                                                <td>{renderStatusBadge(pos.status)}</td>
                                                <td>
                                                    <span className="text-info font-mono small">{pos.amount}</span>
                                                </td>
                                                <td>
                                                    <div className="font-mono" style={{fontSize: '11px', lineHeight: '1.2'}}>
                                                        <div className="mb-1">
                                                            <span className="text-pos me-1">L:</span>
                                                            <span className="text-white-50">{parseFloat(pos.long_entry_target).toFixed(4)}</span>
                                                            <i className="bi bi-arrow-right mx-1 text-muted"></i>
                                                            <span className="text-white-50">{parseFloat(pos.long_exit_target).toFixed(4)}</span>
                                                        </div>
                                                        <div>
                                                            <span className="text-neg me-1">S:</span>
                                                            <span className="text-white-50">{parseFloat(pos.short_entry_target).toFixed(4)}</span>
                                                            <i className="bi bi-arrow-right mx-1 text-muted"></i>
                                                            <span className="text-white-50">{parseFloat(pos.short_exit_target).toFixed(4)}</span>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="text-end">
                                                    <div className="btn-group">
                                                        <button 
                                                            onClick={() => handleOpenInDashboard(pos)}
                                                            className="btn btn-sm btn-dark-custom"
                                                            title="Загрузить в терминал"
                                                        >
                                                            <i className="bi bi-box-arrow-in-up-right"></i>
                                                        </button>
                                                        
                                                        {pos.status !== 'CLOSED' && (
                                                            <button 
                                                                onClick={() => handleClosePosition(pos.id)}
                                                                className="btn btn-sm btn-outline-danger"
                                                                title="Закрыть позицию"
                                                            >
                                                                <i className="bi bi-x-lg"></i>
                                                            </button>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan="6" className="text-center py-5 text-muted small">
                                                Активности не обнаружено
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProfilePage;