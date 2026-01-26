import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

import FundingTablePage from './pages/FundingTablePage';
import ProfilePage from './pages/ProfilePage';
import Login from './pages/Login'; 
import HomePage from './pages/HomePage';
// 1. Импортируем новую страницу
import CoinDetailPage from './pages/CoinDetailPage'; 

function App() {
  return (
    <Router>
      <AuthProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/funding-table" element={<FundingTablePage />} />
            <Route path="/coin/:symbol" element={<CoinDetailPage />} />         
            <Route path="/login" element={<Login />} />
            <Route path="/profile" element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            } />
          </Routes>
        </Layout>
      </AuthProvider>
    </Router>
  );
}

export default App;