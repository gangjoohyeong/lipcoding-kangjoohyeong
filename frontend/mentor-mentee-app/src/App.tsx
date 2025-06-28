import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Navigation from './components/Navigation';
import Login from './components/Login';
import Signup from './components/Signup';
import Profile from './components/Profile';
import Mentors from './components/Mentors';
import Requests from './components/Requests';
import './App.css';

// 인증이 필요한 라우트를 보호하는 컴포넌트
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="loading">로딩 중...</div>;
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

// 인증된 사용자가 로그인/회원가입 페이지에 접근하지 못하도록 하는 컴포넌트
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="loading">로딩 중...</div>;
  }
  
  if (user) {
    return <Navigate to="/profile" replace />;
  }
  
  return <>{children}</>;
};

// 메인 앱 컴포넌트
const AppContent: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="App">
      {user && <Navigation />}
      <Routes>
        {/* 루트 경로 - 인증 상태에 따라 리다이렉트 */}
        <Route path="/" element={
          user ? <Navigate to="/profile" replace /> : <Navigate to="/login" replace />
        } />
        
        {/* 공개 라우트 */}
        <Route path="/login" element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        } />
        <Route path="/signup" element={
          <PublicRoute>
            <Signup />
          </PublicRoute>
        } />
        
        {/* 보호된 라우트 */}
        <Route path="/profile" element={
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        } />
        <Route path="/mentors" element={
          <ProtectedRoute>
            <Mentors />
          </ProtectedRoute>
        } />
        <Route path="/requests" element={
          <ProtectedRoute>
            <Requests />
          </ProtectedRoute>
        } />
      </Routes>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  );
};

export default App;
