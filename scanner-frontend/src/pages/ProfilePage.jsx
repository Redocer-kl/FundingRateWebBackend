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

    // Помощник для отрисовки статуса
    const renderStatusBadge = (status) => {
        const styles = {
            'OPEN': 'bg-success text-white',
            'PENDING': 'bg-warning text-dark',
            'CLOSED': 'bg-secondary text-light'
        };
        return <span className={`badge ${styles[status] || 'bg-dark'} extra-small-badge`}>{status}</span>;
    };

    const handleOpenInDashboard = (pos) => {
        setTradeParams({
            longExchange: pos.long_ticker.exchange,
            shortExchange: pos.short_ticker.exchange,
            symbol: pos.long_ticker.symbol || profile.favorites[0]?.asset_symbol, // Берем из тикера или избранного
            amount: pos.amount,
            longEntry: pos.long_entry_target,
            shortEntry: pos.short_entry_target
        });
        navigate('/'); 
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
                <div className="col-lg-4">
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
                        <h6 className="text-white mb-3 fw-bold">ИЗБРАННОЕ</h6>
                        {profile.favorites?.map(fav => (
                            <div key={fav.id} className="d-flex justify-content-between align-items-center mb-2 p-2 border border-secondary rounded bg-dark-hover">
                                <span className="text-warning fw-bold">{fav.asset_symbol}</span>
                                <Link to={`/coin/${fav.asset_symbol}`} className="btn btn-sm btn-link text-warning p-0">
                                    <i className="bi bi-arrow-right-circle-fill"></i>
                                </Link>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Правая колонка: Все позиции */}
                <div className="col-lg-8">
                    <div className="scanner-card p-4 border border-secondary shadow-lg">
                        <h5 className="text-white mb-4 d-flex align-items-center fw-bold">
                            <i className="bi bi-activity text-warning me-2"></i> 
                            ИСТОРИЯ ПОЗИЦИЙ
                        </h5>
                        
                        <div className="table-responsive">
                            <table className="table table-dark table-hover align-middle border-secondary">
                                <thead className="text-muted small uppercase">
                                    <tr>
                                        <th>Инструмент</th>
                                        <th>Статус</th>
                                        <th>Объем</th>
                                        <th>Цели</th>
                                        <th className="text-end">Действие</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {profile.positions && profile.positions.length > 0 ? (
                                        profile.positions.map(pos => (
                                            <tr key={pos.id} className={pos.status === 'CLOSED' ? 'opacity-50' : ''}>
                                                <td>
                                                    <div className="d-flex flex-column">
                                                        <span className="fw-bold text-white">АРБИТРАЖ #{pos.id}</span>
                                                        <span className="extra-small text-white-50">
                                                            {pos.long_ticker.exchange} / {pos.short_ticker.exchange}
                                                        </span>
                                                    </div>
                                                </td>
                                                <td>{renderStatusBadge(pos.status)}</td>
                                                <td>
                                                    <span className="text-info font-monospace">{pos.amount}</span>
                                                </td>
                                                <td>
                                                    <div className="extra-small text-white-50 ">
                                                        L: {parseFloat(pos.long_entry_target).toFixed(4)} <br/>
                                                        S: {parseFloat(pos.short_entry_target).toFixed(4)}
                                                    </div>
                                                </td>
                                                <td className="text-end">
                                                    <div className="btn-group">
                                                        <button 
                                                            onClick={() => handleOpenInDashboard(pos)}
                                                            className="btn btn-sm btn-outline-warning"
                                                            title="Загрузить в терминал"
                                                        >
                                                            <i className="bi bi-box-arrow-in-up-right"></i>
                                                        </button>
                                                        
                                                        {pos.status !== 'CLOSED' && (
                                                            <button 
                                                                onClick={() => handleClosePosition(pos.id)}
                                                                className="btn btn-sm btn-outline-danger"
                                                                title="Закрыть"
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
                                            <td colSpan="5" className="text-center py-5 text-muted small">
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