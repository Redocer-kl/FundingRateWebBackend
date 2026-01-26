import { useContext, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

const Logout = () => {
    const { logout } = useContext(AuthContext);

    useEffect(() => {
        logout(); // Стираем токены при монтировании компонента
    }, [logout]);

    return <Navigate to="/login" />; // Перенаправляем на вход
};

export default Logout;