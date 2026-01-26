import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import {AuthProvider} from './context/AuthContext'
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Logout from './components/Logout'; 
import ArbitragePage from './pages/ArbitragePage';

import FundingTablePage from './pages/FundingTablePage';
import ProfilePage from './pages/ProfilePage';
import Login from './pages/LoginPage'; 
import RegisterPage from './pages/RegisterPage';
import HomePage from './pages/HomePage';
import CoinDetailPage from './pages/CoinDetailPage'; 
import BestOpportunitiesPage from './pages/BestOpportunitiesPage';
import NotFoundPage from './pages/NotFoundPage'; 

function App() {
  return (
    <Router>
      <AuthProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/funding-table" element={<FundingTablePage />} />
            <Route path="/best-opportunities" element={<BestOpportunitiesPage />} />
            <Route path="/coin/:symbol" element={<CoinDetailPage />} />         
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/orders" element={<ArbitragePage />} />
            
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
    </Router>
  );
}

export default App;