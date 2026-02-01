import React, { useState } from 'react';
import api from '../api';
import { useNavigate, Link } from 'react-router-dom';

const RegisterPage = () => {
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
    });
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (formData.password !== formData.confirmPassword) {
            setError("Пароли не совпадают");
            return;
        }

        try {
            // Отправляем данные на твой RegisterView
            await api.post('register/', {
                username: formData.username,
                email: formData.email,
                password: formData.password
            });
            // После успешной регистрации отправляем на вход
            navigate('/login');
        } catch (err) {
            setError(err.response?.data?.username?.[0] || "Ошибка при регистрации. Возможно, имя уже занято.");
        }
    };

    return (
        <div className="container d-flex justify-content-center align-items-center" style={{ minHeight: '80vh' }}>
            <div className="scanner-card p-4 border border-secondary shadow-lg" style={{ width: '450px', backgroundColor: '#1a1a1a', borderRadius: '15px' }}>
                <h3 className="text-white mb-4 text-center fw-bold">Регистрация</h3>
                
                {error && <div className="alert alert-danger py-2 small">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="mb-3">
                        <label className="text-light small mb-1 text-uppercase">Имя пользователя</label>
                        <input 
                            type="text" 
                            className="form-control bg-dark text-white border-secondary shadow-none" 
                            required
                            onChange={e => setFormData({...formData, username: e.target.value})} 
                        />
                    </div>
                    <div className="mb-3">
                        <label className="text-lightsmall mb-1 text-uppercase">Email</label>
                        <input 
                            type="email" 
                            className="form-control bg-dark text-white border-secondary shadow-none" 
                            required
                            onChange={e => setFormData({...formData, email: e.target.value})} 
                        />
                    </div>
                    <div className="mb-3">
                        <label className="text-light small mb-1 text-uppercase">Пароль</label>
                        <input 
                            type="password" 
                            className="form-control bg-dark text-white border-secondary shadow-none" 
                            required
                            onChange={e => setFormData({...formData, password: e.target.value})} 
                        />
                    </div>
                    <div className="mb-4">
                        <label className="text-light small mb-1 text-uppercase">Повторите пароль</label>
                        <input 
                            type="password" 
                            className="form-control bg-dark text-white border-secondary shadow-none" 
                            required
                            onChange={e => setFormData({...formData, confirmPassword: e.target.value})} 
                        />
                    </div>
                    <button className="btn btn-warning w-100 fw-bold mb-3 py-2 text-dark">Создать аккаунт</button>
                    <div className="text-center small text-light">
                        Уже есть профиль? <Link to="/login" className="text-warning text-decoration-none">Войти</Link>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default RegisterPage;