import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import { toast } from 'react-toastify';

const LoginPage = () => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const { login } = useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(credentials.username, credentials.password);
      toast.success('Успешный вход', { theme: 'dark' });
    } catch (err) {
      toast.error('Ошибка входа. Проверьте данные.', { theme: 'dark' });
    }
  };

  return (
    <div className="container d-flex justify-content-center align-items-center" style={{ minHeight: '80vh' }}>
      <div className="scanner-card p-4 border border-secondary" style={{ width: '400px', backgroundColor: '#1a1a1a' }}>
        <h3 className="text-white mb-4 text-center">Вход в систему</h3>
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="text-light small mb-1">Username</label>
            <input
              type="text"
              className="form-control bg-dark text-white border-secondary shadow-none"
              value={credentials.username}
              onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
            />
          </div>
          <div className="mb-4">
            <label className="text-light small mb-1">Password</label>
            <input
              type="password"
              className="form-control bg-dark text-white border-secondary shadow-none"
              value={credentials.password}
              onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
            />
          </div>
          <button className="btn btn-warning w-100 fw-bold mb-3">Войти</button>
          <div className="text-center small text-light">
            Нет аккаунта? <Link to="/register" className="text-warning">Создать</Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
