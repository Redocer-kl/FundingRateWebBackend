import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { TradeProvider } from './context/TradeContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Logout from './components/Logout'; 

import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import FundingTablePage from './pages/FundingTablePage';
import ProfilePage from './pages/ProfilePage';
import Login from './pages/LoginPage'; 
import RegisterPage from './pages/RegisterPage';
import HomePage from './pages/HomePage';
import CoinDetailPage from './pages/CoinDetailPage'; 
import BestOpportunitiesPage from './pages/BestOpportunitiesPage';
import NotFoundPage from './pages/NotFoundPage';
import DashboardPage from './pages/DashboardPage'; 

function App() {
  return (
    <Router>
      <TradeProvider>
        <AuthProvider>
          <Layout>
            {/* Контейнер для тостов будет доступен на всех страницах */}
            <ToastContainer 
              position="bottom-right"
              autoClose={3000}
              hideProgressBar={false}
              newestOnTop={false}
              closeOnClick
              rtl={false}
              pauseOnFocusLoss
              draggable
              pauseOnHover
              theme="dark"
            />
            
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/funding-table" element={<FundingTablePage />} />
              <Route path="/best-opportunities" element={<BestOpportunitiesPage />} />
              <Route path="/coin/:symbol" element={<CoinDetailPage />} />         
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              
              <Route path="/logout" element={<Logout />} />

              <Route 
                path="/profile" 
                element={
                  <ProtectedRoute>
                    <ProfilePage />
                  </ProtectedRoute>
                } 
              />

              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </Layout>
        </AuthProvider>
      </TradeProvider>
    </Router>
  );
}

export default App;