import React, { useEffect, useState, useContext } from 'react';
import api from '../api';
import { AuthContext } from '../context/AuthContext';
import { Link } from 'react-router-dom';

const ProfilePage = () => {
    const [profile, setProfile] = useState(null);
    const { logout } = useContext(AuthContext);

    useEffect(() => {
        api.get('profile/')
            .then(res => setProfile(res.data))
            .catch(err => console.error(err));
    }, []);

    if (!profile) return (
        <div className="d-flex justify-content-center align-items-center" style={{minHeight: '50vh'}}>
            <div className="spinner-border text-warning" role="status"></div>
            <span className="ms-3 text-light">Загрузка профиля...</span>
        </div>
    );

    return (
        <div className="container py-5">
            <div className="row g-4">
                {/* Информация о юзере */}
                <div className="col-lg-4">
                    <div className="scanner-card p-4 border border-secondary shadow-lg">
                        <div className="text-center mb-4">
                            <div className="profile-avatar mx-auto mb-3">
                                <i className="bi bi-person-fill"></i>
                            </div>
                            <h4 className="text-white fw-bold mb-1">{profile.username}</h4>
                            {/* Заменили text-muted на custom-muted для читаемости */}
                            <p className="custom-muted small mb-0">{profile.email}</p>
                        </div>
                        <hr className="border-secondary opacity-25" />
                        <button onClick={logout} className="btn btn-outline-danger w-100 btn-sm fw-bold py-2">
                            <i className="bi bi-box-arrow-right me-2"></i> ВЫЙТИ ИЗ СИСТЕМЫ
                        </button>
                    </div>
                </div>

                {/* Список Избранного */}
                <div className="col-lg-8">
                    <div className="scanner-card p-4 border border-secondary shadow-lg">
                        <h5 className="text-white mb-4 d-flex align-items-center">
                            <i className="bi bi-star-fill text-warning me-2"></i> 
                            Ваше Избранное
                        </h5>
                        
                        {profile.favorites && profile.favorites.length > 0 ? (
                            <div className="row g-3">
                                {profile.favorites.map(fav => (
                                    <div key={fav.asset_symbol} className="col-md-6">
                                        <div className="favorite-item p-3 rounded d-flex justify-content-between align-items-center border border-secondary">
                                            <div className="d-flex align-items-center">
                                                <span className="fw-bold text-warning fs-5">{fav.asset_symbol}</span>
                                            </div>
                                            <Link to={`/coin/${fav.asset_symbol}`} className="btn btn-sm btn-warning fw-bold px-3">
                                                АНАЛИЗ
                                            </Link>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-5 empty-state">
                                <i className="bi bi-stars mb-3 d-block opacity-50"></i>
                                <p className="text-light fs-5 mb-1">Список пуст</p>
                                <p className="custom-muted small">Добавляйте монеты в избранное, чтобы они появились здесь</p>
                                <Link to="/funding-table" className="btn btn-sm btn-outline-warning mt-3">Перейти к таблице</Link>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProfilePage;