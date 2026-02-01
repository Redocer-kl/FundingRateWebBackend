import React, { useEffect, useState, useContext } from 'react';
import api from '../api';
import { AuthContext } from '../context/AuthContext';
import { TradeContext } from '../context/TradeContext';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { ethers } from 'ethers';


const ExchangeModal = ({ exchange, onClose, onSuccess }) => {
    const [formData, setFormData] = useState({
        api_key: '',
        api_secret: '',
        passphrase: '',
    });
    const [loading, setLoading] = useState(false);

    const exchangeConfigs = {
        'Binance': {
            text: 'Создайте API Key (HMAC). Включите "Enable Reading", "Enable Spot & Margin Trading" и "Enable Futures".',
            link: 'https://www.binance.com/en/my/settings/api-management'
        },
        'Bybit': {
            text: 'Выберите "System-generated API Keys". Права: "Read-Write". В разделах "Unified Trading" отметьте "Order" и "Position".',
            link: 'https://www.bybit.com/app/user/api-management'
        },
        'Kucoin': {
            text: 'Создайте API с типом "Trade". Обязательно запомните Passphrase. Разрешите "Spot" и "Futures" торговлю.',
            link: 'https://www.kucoin.com/account/api'
        },
        'Bitget': {
            text: 'Создайте ключ для "System-generated". Требуется Passphrase. Права: "Order" и "Holdings" в разделе "Futures".',
            link: 'https://www.bitget.com/export/api'
        }
    };

    const currentConfig = exchangeConfigs[exchange.name] || { text: 'Введите ваши ключи.', link: '#' };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await api.post('keys/credentials/', {
                exchange_name: exchange.name,
                api_key: formData.api_key,
                api_secret: formData.api_secret,
                passphrase: formData.passphrase
            });
            toast.success(`Ключи для ${exchange.name} успешно привязаны!`);
            onSuccess();
            onClose();
        } catch (err) {
            const errorData = err.response?.data;
            const errorMsg = typeof errorData === 'object' ? JSON.stringify(errorData) : (errorData || 'Ошибка сохранения');
            toast.error(`Ошибка: ${errorMsg}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal d-block shadow-lg" style={{ backgroundColor: 'rgba(0,0,0,0.85)', zIndex: 1050 }}>
            <div className="modal-dialog modal-dialog-centered">
                <div className="modal-content bg-dark border-secondary text-white">
                    <div className="modal-header border-bottom border-secondary">
                        <h5 className="modal-title text-warning fw-bold">
                            <i className="bi bi-shield-lock me-2"></i>{exchange.name} API
                        </h5>
                        <button type="button" className="btn-close btn-close-white" onClick={onClose}></button>
                    </div>
                    <form onSubmit={handleSubmit}>
                        <div className="modal-body p-4">
                            <div className="p-3 mb-4 rounded border border-warning-subtle small text-warning" style={{ backgroundColor: 'rgba(255,193,7,0.05)' }}>
                                <div className="mb-2"><strong><i className="bi bi-info-circle me-1"></i> Инструкция:</strong></div>
                                {currentConfig.text}
                                <div className="mt-2">
                                    <a href={currentConfig.link} target="_blank" rel="noopener noreferrer" className="text-decoration-none text-info fw-bold">
                                        Перейти к созданию ключа <i className="bi bi-box-arrow-up-right ms-1"></i>
                                    </a>
                                </div>
                            </div>

                            <div className="mb-3">
                                <label className="form-label text-white-50 small fw-bold">API KEY</label>
                                <input
                                    type="text"
                                    className="form-control form-control-sm bg-dark text-white border-secondary shadow-none"
                                    required
                                    onChange={e => setFormData({ ...formData, api_key: e.target.value })}
                                />
                            </div>
                            <div className="mb-3">
                                <label className="form-label text-white-50 small fw-bold">API SECRET</label>
                                <input
                                    type="password"
                                    className="form-control form-control-sm bg-dark text-white border-secondary shadow-none"
                                    required
                                    onChange={e => setFormData({ ...formData, api_secret: e.target.value })}
                                />
                            </div>
                            {(exchange.name === 'Kucoin' || exchange.name === 'Bitget') && (
                                <div className="mb-3">
                                    <label className="form-label text-white-50 small fw-bold">API PASSPHRASE</label>
                                    <input
                                        type="text"
                                        className="form-control form-control-sm bg-dark text-white border-secondary shadow-none"
                                        required
                                        onChange={e => setFormData({ ...formData, passphrase: e.target.value })}
                                    />
                                </div>
                            )}
                        </div>
                        <div className="modal-footer border-top border-secondary">
                            <button type="button" className="btn btn-sm btn-outline-secondary" onClick={onClose}>ОТМЕНА</button>
                            <button type="submit" className="btn btn-sm btn-warning px-4 fw-bold" disabled={loading}>
                                {loading ? 'СОХРАНЕНИЕ...' : 'СОХРАНИТЬ'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

const ProfilePage = () => {
    const [profile, setProfile] = useState(null);
    const [credentials, setCredentials] = useState([]);
    const [showModal, setShowModal] = useState(null);
    const { logout } = useContext(AuthContext);
    const { setTradeParams } = useContext(TradeContext);

    const [hlAgent, setHlAgent] = useState(null);
    const [isHlLoading, setIsHlLoading] = useState(false);

    const [paradexAgent, setParadexAgent] = useState(null);
    const [isParadexLoading, setIsParadexLoading] = useState(false);

    const navigate = useNavigate();


    const availableExchanges = [
        { name: 'Binance', icon: 'bi-currency-bitcoin' },
        { name: 'Bybit', icon: 'bi-graph-up' },
        { name: 'Kucoin', icon: 'bi-wallet2' },
        { name: 'Bitget', icon: 'bi-shield-check' }
    ];

    const fetchProfileData = async () => {
        try {
            const [profRes, credRes, hlRes, pdxRes] = await Promise.all([
                api.get('profile/'),
                api.get('keys/credentials/'),
                api.get('keys/hl-generate/'),
                api.get('keys/paradex-generate/')
            ]);
            setProfile(profRes.data);
            setCredentials(credRes.data);

            if (hlRes.data && hlRes.data.agent_address) {
                setHlAgent(hlRes.data);
            }
            if (pdxRes.data?.account_address) setParadexAgent(pdxRes.data);
        } catch (err) {
            console.error(err);
            toast.error("Ошибка загрузки данных профиля");
        }
    };

    useEffect(() => {
        fetchProfileData();
    }, []);

    const handleCreateHlAgent = async () => {
        setIsHlLoading(true);
        try {
            const res = await api.post('keys/hl-generate/');
            setHlAgent(res.data);
            toast.success("Агент создан. Теперь необходимо подтверждение в MetaMask");
        } catch (err) {
            toast.error("Ошибка при создании агента");
        } finally {
            setIsHlLoading(false);
        }
    };

    const handleApproveHlAgent = async () => {
        if (!window.ethereum) {
            toast.info(
                <div>
                    MetaMask не найден.
                    <br />
                    <a href="https://metamask.io/download/" target="_blank" rel="noreferrer" className="btn btn-sm btn-warning mt-2">
                        Установить MetaMask
                    </a>
                </div>,
                { autoClose: 10000 }
            );
            return;
        }

        setIsHlLoading(true);
        try {
            const provider = new ethers.BrowserProvider(window.ethereum);

            // Запрашиваем доступ к аккаунту, если еще не подключен
            await window.ethereum.request({ method: 'eth_requestAccounts' });

            const signer = await provider.getSigner();

            const domain = {
                name: "Exchange",
                version: "1",
                chainId: 42161,
                verifyingContract: "0x0000000000000000000000000000000000000000"
            };

            const types = {
                "HyperliquidTransaction:ApproveAgent": [
                    { name: "hyperliquidChain", type: "string" },
                    { name: "agentAddress", type: "address" },
                    { name: "agentName", type: "string" },
                    { name: "nonce", type: "uint64" }
                ]
            };

            const message = {
                hyperliquidChain: "Mainnet",
                agentAddress: hlAgent.agent_address,
                agentName: "ArbitrageBot",
                nonce: Date.now()
            };

            const signature = await signer.signTypedData(domain, types, message);

            await api.post('keys/hl-approve/', {
                signature: signature,
                payload: message
            });

            toast.success("Доступ агенту разрешен в блокчейне!");
            fetchProfileData();
        } catch (err) {
            console.error(err);
            toast.error("Ошибка Approve: " + (err.message || "Отменено"));
        } finally {
            setIsHlLoading(false);
        }
    };

    const handleCreateParadexAgent = async () => {
        setIsParadexLoading(true);
        try {
            const res = await api.post('keys/paradex-generate/');
            setParadexAgent(res.data);
            toast.success("Paradex аккаунт инициализирован");
        } catch (err) { toast.error("Ошибка создания Paradex агента"); }
        finally { setIsParadexLoading(false); }
    };

    const handleApproveParadex = async () => {
        if (!window.ethereum) return toast.error("MetaMask не найден");
        setIsParadexLoading(true);
        try {
            const provider = new ethers.BrowserProvider(window.ethereum);
            const signer = await provider.getSigner();

            const domain = { name: "Paradex", version: "1", chainId: 1 }; 
            const types = {
                "ParadexTransaction:Onboarding": [
                    { name: "action", type: "string" },
                    { name: "account", type: "address" }
                ]
            };
            const message = {
                action: "Onboarding",
                account: paradexAgent.account_address
            };

            const signature = await signer.signTypedData(domain, types, message);
            
            await api.post('keys/paradex-approve/', {
                signature: signature,
                account_address: paradexAgent.account_address
            });

            toast.success("Paradex успешно привязан!");
            fetchProfileData();
        } catch (err) {
            console.error(err);
            toast.error("Ошибка Paradex Approve");
        } finally {
            setIsParadexLoading(false);
        }
    };

    const getCredential = (exchangeName) => {
        return credentials.find(c => c.display_name === exchangeName);
    };

    const handleDeleteCredential = async (exchangeName) => {
        const cred = getCredential(exchangeName);
        if (!cred) return;

        if (window.confirm(`Вы уверены, что хотите удалить ключи для ${exchangeName}?`)) {
            try {
                await api.delete('keys/credentials/', { data: { id: cred.id } });
                toast.success(`Ключи для ${exchangeName} успешно удалены`);
                fetchProfileData();
            } catch (err) {
                console.error(err);
                toast.error("Не удалось удалить ключи");
            }
        }
    };

    const renderStatusBadge = (status) => {
        const styles = {
            'OPEN': 'bg-success text-white',
            'PENDING': 'bg-warning text-dark',
            'CLOSED': 'bg-secondary text-light'
        };
        return <span className={`badge ${styles[status] || 'bg-dark'} extra-small-badge`} style={{ fontSize: '10px' }}>{status}</span>;
    };

    const handleOpenInDashboard = (pos) => {
        setTradeParams({
            longExchange: pos.long_ticker.exchange,
            shortExchange: pos.short_ticker.exchange,
            symbol: pos.long_ticker.symbol,
            amount: pos.amount,
            longEntry: pos.long_entry_target,
            shortEntry: pos.short_entry_target,
            longExit: pos.long_exit_target,
            shortExit: pos.short_exit_target
        });
        navigate('/dashboard');
    };

    const handleClosePosition = async (id) => {
        if (window.confirm("Вы уверены, что хотите закрыть эту позицию?")) {
            const toastId = toast.loading("Закрытие позиции на бирже...");
            try {
                await api.post(`positions/${id}/close/`);
                toast.update(toastId, { render: "Позиция успешно закрыта", type: "success", isLoading: false, autoClose: 3000 });
                fetchProfileData();
            } catch (err) {
                console.error("Ошибка при закрытии:", err);
                toast.update(toastId, { render: "Не удалось закрыть позицию", type: "error", isLoading: false, autoClose: 3000 });
            }
        }
    };

    if (!profile) return (
        <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '50vh' }}>
            <div className="spinner-border text-warning" role="status"></div>
            <span className="ms-3 text-light">Загрузка профиля...</span>
        </div>
    );

    return (
        <div className="container py-5">
            {showModal && (
                <ExchangeModal
                    exchange={showModal}
                    onClose={() => setShowModal(null)}
                    onSuccess={fetchProfileData}
                />
            )}

            <div className="row g-4">
                <div className="col-lg-3">
                    <div className="scanner-card p-4 border border-secondary shadow-lg mb-4">
                        <div className="text-center mb-4">
                            <div className="profile-avatar mx-auto mb-3">
                                <i className="bi bi-person-circle text-warning fs-1"></i>
                            </div>
                            <h4 className="text-white fw-bold mb-1">{profile.username}</h4>
                            <p className="custom-muted small mb-0">{profile.email}</p>
                        </div>
                        <button onClick={logout} className="btn btn-outline-danger w-100 btn-sm fw-bold">ВЫЙТИ</button>
                    </div>

                    {/* Секция Hyperliquid*/}
                    <div className="scanner-card p-4 border border-secondary shadow-lg mb-4 bg-dark">
                        <h6 className="text-white mb-3 fw-bold small d-flex justify-content-between align-items-center">
                            HYPERLIQUID AGENT
                            <i className="bi bi-lightning-fill text-info"></i>
                        </h6>
                        {!hlAgent ? (
                            <button
                                onClick={handleCreateHlAgent}
                                disabled={isHlLoading}
                                className="btn btn-sm btn-warning w-100 fw-bold"
                            >
                                {isHlLoading ? 'ГЕНЕРАЦИЯ...' : 'СОЗДАТЬ АГЕНТА'}
                            </button>
                        ) : (
                            <div className="p-2 border border-secondary rounded">
                                <div className="small text-white-50 mb-2">Адрес агента:</div>
                                <div className="font-mono extra-small text-warning text-truncate mb-3">
                                    {hlAgent.agent_address}
                                </div>
                                {hlAgent.is_approved ? (
                                    <div className="text-success small fw-bold text-center">
                                        <i className="bi bi-check-circle-fill me-1"></i> АКТИВЕН
                                    </div>
                                ) : (
                                    <button
                                        onClick={handleApproveHlAgent}
                                        disabled={isHlLoading}
                                        className="btn btn-sm btn-outline-info w-100 fw-bold"
                                    >
                                        {isHlLoading ? 'ПОДПИСЬ...' : 'APPROVE В METAMASK'}
                                    </button>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Секция Paradex  */}

                    <div className="scanner-card p-4 border border-secondary shadow-lg mb-4 bg-dark">
                        <h6 className="text-white mb-3 fw-bold small d-flex justify-content-between">
                            PARADEX (L2) <i className="bi bi-layers-half text-danger"></i>
                        </h6>
                        {!paradexAgent ? (
                            <button 
                                onClick={handleCreateParadexAgent} 
                                disabled={isParadexLoading} 
                                className="btn btn-sm btn-danger w-100 fw-bold"
                            >
                                {isParadexLoading ? 'ГЕНЕРАЦИЯ...' : 'ПОДКЛЮЧИТЬ PARADEX'}
                            </button>
                        ) : (
                            <div className="p-2 border border-secondary rounded">
                                <div className="small text-white-50 mb-1">Account:</div>
                                <div className="extra-small text-danger text-truncate mb-3 font-mono">
                                    {paradexAgent.account_address}
                                </div>
                                {paradexAgent.is_approved ? (
                                    <div className="text-success small fw-bold text-center">
                                        <i className="bi bi-shield-check me-1"></i> ГОТОВ К ТОРГАМ
                                    </div>
                                ) : (
                                    <button 
                                        onClick={handleApproveParadex} 
                                        disabled={isParadexLoading} 
                                        className="btn btn-sm btn-outline-danger w-100 fw-bold"
                                    >
                                        {isParadexLoading ? 'ПОДПИСЬ...' : 'ONBOARDING L2'}
                                    </button>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Обычные API */}
                    <div className="scanner-card p-4 border border-secondary shadow-lg mb-4">
                        <h6 className="text-white mb-3 fw-bold small d-flex justify-content-between align-items-center">
                            API ПОДКЛЮЧЕНИЯ
                            <i className="bi bi-plug-fill text-warning"></i>
                        </h6>
                        <div className="d-grid gap-2">
                            {availableExchanges.map(ex => {
                                const cred = getCredential(ex.name);
                                const isConnected = !!cred;
                                const isValid = cred?.is_valid;
                                return (
                                    <div key={ex.name} className="d-flex gap-1">
                                        <button
                                            onClick={() => setShowModal(ex)}
                                            className={`btn btn-sm d-flex justify-content-between align-items-center border flex-grow-1 ${isConnected
                                                ? (isValid ? 'btn-dark border-success text-success' : 'btn-dark border-danger text-danger')
                                                : 'btn-dark border-secondary text-light opacity-75'
                                                }`}
                                        >
                                            <span style={{ fontSize: '12px' }}><i className={`bi ${ex.icon} me-2`}></i>{ex.name}</span>
                                            {isConnected ? <i className={`bi ${isValid ? 'bi-check2-circle' : 'bi-exclamation-triangle'}`}></i> : <i className="bi bi-plus-lg"></i>}
                                        </button>
                                        {isConnected && (
                                            <button onClick={() => handleDeleteCredential(ex.name)} className="btn btn-sm btn-outline-danger border-secondary">
                                                <i className="bi bi-trash"></i>
                                            </button>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>

                <div className="col-lg-9">
                    <div className="scanner-card p-4 border border-secondary shadow-lg">
                        <h5 className="text-white mb-4 d-flex align-items-center fw-bold">
                            <i className="bi bi-activity text-warning me-2"></i>
                            ЖУРНАЛ ТОРГОВЛИ
                        </h5>

                        <div className="table-responsive">
                            <table className="table table-dark table-hover align-middle border-secondary">
                                <thead className="text-white-50 small">
                                    <tr style={{ fontSize: '11px' }}>
                                        <th>ID / ТИКЕР</th>
                                        <th>БИРЖИ (L/S)</th>
                                        <th>СТАТУС</th>
                                        <th>ОБЪЕМ</th>
                                        <th>ЦЕЛИ (IN / OUT)</th>
                                        <th className="text-end">ДЕЙСТВИЕ</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {profile.positions && profile.positions.length > 0 ? (
                                        profile.positions.map(pos => (
                                            <tr key={pos.id} className={pos.status === 'CLOSED' ? 'opacity-50' : ''}>
                                                <td>
                                                    <div className="d-flex flex-column">
                                                        <span className="fw-bold text-white small">#{pos.id}</span>
                                                        <span className="text-warning font-mono" style={{ fontSize: '12px' }}>
                                                            {pos.long_ticker.symbol}
                                                        </span>
                                                    </div>
                                                </td>
                                                <td>
                                                    <div className="d-flex flex-column small">
                                                        <span className="text-pos">{pos.long_ticker.exchange}</span>
                                                        <span className="text-neg">{pos.short_ticker.exchange}</span>
                                                    </div>
                                                </td>
                                                <td>{renderStatusBadge(pos.status)}</td>
                                                <td>
                                                    <span className="text-info font-mono small">{pos.amount}</span>
                                                </td>
                                                <td>
                                                    <div className="font-mono" style={{ fontSize: '11px', lineHeight: '1.2' }}>
                                                        <div className="mb-1">
                                                            <span className="text-pos me-1">L:</span>
                                                            <span className="text-white-50">{parseFloat(pos.long_entry_target).toFixed(4)}</span>
                                                            <i className="bi bi-arrow-right mx-1 text-white-50"></i>
                                                            <span className="text-white-50">{parseFloat(pos.long_exit_target).toFixed(4)}</span>
                                                        </div>
                                                        <div>
                                                            <span className="text-neg me-1">S:</span>
                                                            <span className="text-white-50">{parseFloat(pos.short_entry_target).toFixed(4)}</span>
                                                            <i className="bi bi-arrow-right mx-1 text-white-50"></i>
                                                            <span className="text-white-50">{parseFloat(pos.short_exit_target).toFixed(4)}</span>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="text-end">
                                                    <div className="btn-group">
                                                        <button
                                                            onClick={() => handleOpenInDashboard(pos)}
                                                            className="btn btn-sm btn-dark-custom"
                                                            title="Загрузить в терминал"
                                                        >
                                                            <i className="bi bi-box-arrow-in-up-right"></i>
                                                        </button>

                                                        {pos.status !== 'CLOSED' && (
                                                            <button
                                                                onClick={() => handleClosePosition(pos.id)}
                                                                className="btn btn-sm btn-outline-danger"
                                                                title="Закрыть позицию"
                                                            >
                                                                <i className="bi bi-x-lg"></i>
                                                            </button>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan="6" className="text-center py-5 text-white-50 small">
                                                Активности не обнаружено
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProfilePage;