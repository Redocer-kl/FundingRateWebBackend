import React, { useState } from 'react';
import api from '../api';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'react-toastify';

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      toast.warn('Пароли не совпадают', { theme: 'dark' });
      return;
    }

    try {
      await api.post('api/register/', {
        username: formData.username,
        email: formData.email,
        password: formData.password
      });
      toast.success(
        <div>
          <strong>✅ Регистрация успешна</strong>
          <div className="small opacity-75">Войдите в аккаунт</div>
        </div>,
        { theme: 'dark' }
      );
      navigate('/login');
    } catch (err) {
      const message = err.response?.data?.username?.[0] || err.response?.data || 'Ошибка при регистрации. Возможно, имя уже занято.';
      const text = typeof message === 'string' ? message : JSON.stringify(message);
      toast.error(`❌ ${text}`, { theme: 'dark' });
    }
  };

  return (
    <div className="container d-flex justify-content-center align-items-center" style={{ minHeight: '80vh' }}>
      <div className="scanner-card p-4 border border-secondary shadow-lg" style={{ width: '450px', backgroundColor: '#1a1a1a', borderRadius: '15px' }}>
        <h3 className="text-white mb-4 text-center fw-bold">Регистрация</h3>
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="text-light small mb-1 text-uppercase">Имя пользователя</label>
            <input
              type="text"
              className="form-control bg-dark text-white border-secondary shadow-none"
              required
              value={formData.username}
              onChange={e => setFormData({ ...formData, username: e.target.value })}
            />
          </div>
          <div className="mb-3">
            <label className="text-light small mb-1 text-uppercase">Email</label>
            <input
              type="email"
              className="form-control bg-dark text-white border-secondary shadow-none"
              required
              value={formData.email}
              onChange={e => setFormData({ ...formData, email: e.target.value })}
            />
          </div>
          <div className="mb-3">
            <label className="text-light small mb-1 text-uppercase">Пароль</label>
            <input
              type="password"
              className="form-control bg-dark text-white border-secondary shadow-none"
              required
              value={formData.password}
              onChange={e => setFormData({ ...formData, password: e.target.value })}
            />
          </div>
          <div className="mb-4">
            <label className="text-light small mb-1 text-uppercase">Повторите пароль</label>
            <input
              type="password"
              className="form-control bg-dark text-white border-secondary shadow-none"
              required
              value={formData.confirmPassword}
              onChange={e => setFormData({ ...formData, confirmPassword: e.target.value })}
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
