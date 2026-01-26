import { Link, useNavigate } from 'react-router-dom';
import { useContext } from 'react';
import AuthContext from '../context/AuthContext';

const Layout = ({ children }) => {
    const { user, logoutUser } = useContext(AuthContext);
    const navigate = useNavigate();

    return (
        <div>
            <nav className="navbar navbar-expand-lg navbar-dark bg-dark border-bottom border-secondary mb-4">
                <div className="container">
                    <Link className="navbar-brand fw-bold" to="/">
                        Funding <span className="text-warning">Scanner</span>
                    </Link>
                    
                    <div className="d-flex align-items-center gap-3">
                        <Link to="/" className="text-decoration-none text-light">Таблица</Link>
                        <Link to="/best" className="text-decoration-none text-light">Связки</Link>
                        
                        {user ? (
                            <div className="dropdown">
                                <button className="btn btn-outline-warning btn-sm dropdown-toggle" type="button" data-bs-toggle="dropdown">
                                    {user.username}
                                </button>
                                <ul className="dropdown-menu dropdown-menu-dark">
                                    <li><Link className="dropdown-item" to="/profile">Профиль</Link></li>
                                    <li><button className="dropdown-item" onClick={logoutUser}>Выйти</button></li>
                                </ul>
                            </div>
                        ) : (
                            <Link to="/login" className="btn btn-warning btn-sm fw-bold">Войти</Link>
                        )}
                    </div>
                </div>
            </nav>
            <div className="container pb-5">
                {children}
            </div>
        </div>
    );
};

export default Layout;