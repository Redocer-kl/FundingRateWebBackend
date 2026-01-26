import { createContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    const login = async (username, password) => {
        const res = await api.post('token/', { username, password });
        localStorage.setItem('access', res.data.access);
        localStorage.setItem('refresh', res.data.refresh);
        // Сохраняем имя пользователя
        localStorage.setItem('username', username);
        setUser({ username });
        navigate('/profile');
    };

    const logout = () => {
        localStorage.removeItem('access');
        localStorage.removeItem('refresh');
        localStorage.removeItem('username');
        setUser(null);
        navigate('/login');
    };

    useEffect(() => {
        const token = localStorage.getItem('access');
        const storedUsername = localStorage.getItem('username');
        
        if (token && storedUsername) {
            // Теперь user — это объект, а не просто true
            setUser({ username: storedUsername });
        }
        setLoading(false);
    }, []);

    return (
        <AuthContext.Provider value={{ user, login, logout, loading }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};