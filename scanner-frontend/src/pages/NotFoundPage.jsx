import { Link } from 'react-router-dom';

const NotFoundPage = () => {
    return (
        <div className="container text-center py-5" style={{ minHeight: '70vh', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <h1 className="display-1 fw-bold text-warning">404</h1>
            <h2 className="text-white mb-4">Упс! Страница не найдена</h2>
            <p className="text-muted mb-5">Похоже, эта монета еще не прошла листинг или путь был указан неверно.</p>
            <div>
                <Link to="/" className="btn btn-warning fw-bold px-4 py-2">
                    Вернуться на главную
                </Link>
            </div>
        </div>
    );
};

export default NotFoundPage;