import { Link, useNavigate, NavLink } from 'react-router-dom';
import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext'; 

const Layout = ({ children }) => {
    const { user, logout } = useContext(AuthContext);
    const navigate = useNavigate();

    return (
        <div style={{ minHeight: '100vh', backgroundColor: '#000' }}>
            <nav className="navbar navbar-expand-lg navbar-dark bg-dark border-bottom border-secondary mb-4 sticky-top">
                <div className="container">
                    <Link className="navbar-brand fw-bold" to="/">
                        <i className="bi bi-lightning-charge-fill text-warning me-1"></i>
                        Funding <span className="text-warning">Scanner</span>
                    </Link>
                    
                    <div className="d-flex align-items-center gap-4">
                        <NavLink 
                            to="/funding-table" 
                            className={({isActive}) => `text-decoration-none small fw-bold ${isActive ? 'text-warning' : 'text-light opacity-75'}`}
                        >
                            ТАБЛИЦА
                        </NavLink>
                        
                        <NavLink 
                            to="/best-opportunities" 
                            className={({isActive}) => `text-decoration-none small fw-bold ${isActive ? 'text-warning' : 'text-light opacity-75'}`}
                        >
                            СВЯЗКИ
                        </NavLink>
                        
                        <div className="vr text-secondary mx-2" style={{height: '20px'}}></div>

                        {user ? (
                            <div className="dropdown">
                                <button 
                                    className="btn btn-sm btn-outline-warning dropdown-toggle px-3 border-secondary" 
                                    type="button" 
                                    id="profileDropdown"
                                    data-bs-toggle="dropdown" 
                                    aria-expanded="false"
                                >
                                    <i className="bi bi-person-circle me-2"></i>
                                    {/* Если объекта user нет или он пустой, покажем "Аккаунт" */}
                                    {user.username ? user.username : "Аккаунт"}
                                </button>
                                <ul className="dropdown-menu dropdown-menu-dark dropdown-menu-end shadow-lg border-secondary" aria-labelledby="profileDropdown">
                                    <li>
                                        {/* Используем Link, чтобы переход был мгновенным без перезагрузки */}
                                        <Link className="dropdown-item py-2" to="/profile">
                                            <i className="bi bi-person-vcard me-2"></i>Личный кабинет
                                        </Link>
                                    </li>
                                    <li><hr className="dropdown-divider border-secondary" /></li>
                                    <li>
                                        <button className="dropdown-item py-2 text-danger" onClick={logout}>
                                            <i className="bi bi-box-arrow-right me-2"></i>Выйти
                                        </button>
                                    </li>
                                </ul>
                            </div>
                        ) : (
                            <Link to="/login" className="btn btn-sm btn-warning fw-bold px-3">Войти</Link>
                        )}
                                            </div>
                                        </div>
                                    </nav>

                                    <main className="container pb-5">
                                        {children}
                                    </main>
                                </div>
                            );
                        };

export default Layout;