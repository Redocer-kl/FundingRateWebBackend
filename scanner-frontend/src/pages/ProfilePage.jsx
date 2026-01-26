// src/pages/ProfilePage.jsx
import { useEffect, useState, useContext } from 'react';
import api from '../api'; // Выходим из pages в src
import AuthContext from '../context/AuthContext'; // Выходим из pages в src -> context
import { Link } from 'react-router-dom';

const ProfilePage = () => {
    const { user } = useContext(AuthContext);
    const [profileData, setProfileData] = useState(null);

    useEffect(() => {
        // Запрос к бекенду за профилем
        api.get('profile/')
            .then(res => setProfileData(res.data))
            .catch(err => console.error(err));
    }, []);

    if (!profileData) return <div className="text-white p-4">Загрузка профиля...</div>;

    return (
        <div className="row">
            <div className="col-md-4 mb-4">
                <div className="scanner-card text-center">
                    <div className="bg-warning rounded-circle d-inline-flex align-items-center justify-content-center mb-3" style={{width: 80, height: 80}}>
                        <span className="h1 text-dark mb-0">{user?.username?.[0]?.toUpperCase()}</span>
                    </div>
                    <h3 className="text-white">{user?.username}</h3>
                    <p className="text-muted">{profileData.email}</p>
                </div>
            </div>

            <div className="col-md-8">
                <div className="scanner-card">
                    <h4 className="text-white mb-4 border-bottom border-secondary pb-3">
                        <i className="bi bi-star-fill text-warning me-2"></i> 
                        Избранные активы
                    </h4>
                    
                    {profileData.favorites.length === 0 ? (
                        <p className="text-muted">Вы пока ничего не добавили в избранное.</p>
                    ) : (
                        <div className="list-group list-group-flush">
                            {profileData.favorites.map(fav => (
                                <div key={fav.id} className="list-group-item bg-transparent border-secondary d-flex justify-content-between align-items-center px-0">
                                    <span className="text-white fw-bold">{fav.asset_symbol}</span>
                                    <span className="badge bg-secondary">{fav.exchange_name}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ProfilePage;