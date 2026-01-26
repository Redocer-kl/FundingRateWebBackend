import { useContext, useState } from 'react';
import AuthContext from '../context/AuthContext'; // Обрати внимание на две точки

const Login = () => {
    const { loginUser } = useContext(AuthContext);
    
    // Локальное состояние для полей ввода
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        // Вызываем функцию логина из контекста
        username.length > 0 && loginUser(username, password);
    };

    return (
        <div className="row justify-content-center mt-5">
            <div className="col-md-5 col-lg-4">
                <div className="scanner-card">
                    <h3 className="text-white text-center mb-4">Вход</h3>
                    <form onSubmit={handleSubmit}>
                        <div className="mb-3">
                            <label className="text-muted small">Логин</label>
                            <input 
                                type="text" 
                                className="form-control bg-dark text-white border-secondary" 
                                placeholder="Введите имя пользователя"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                            />
                        </div>
                        <div className="mb-4">
                            <label className="text-muted small">Пароль</label>
                            <input 
                                type="password" 
                                className="form-control bg-dark text-white border-secondary" 
                                placeholder="Введите пароль"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                        <button type="submit" className="btn btn-warning w-100 fw-bold">
                            Войти
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default Login;