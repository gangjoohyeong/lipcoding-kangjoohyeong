import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Navigation.css';

const Navigation: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user) return null;

  return (
    <nav className="navigation">
      <div className="nav-container">
        <div className="nav-brand">
          <Link to="/profile" className="brand-link">
            Mentor-Mentee
          </Link>
        </div>
        
        <div className="nav-links">
          <Link to="/profile" className="nav-link">
            프로필
          </Link>
          
          {user.role === 'mentee' && (
            <Link to="/mentors" className="nav-link">
              멘토
            </Link>
          )}
          
          <Link to="/requests" className="nav-link">
            요청
          </Link>
          
          <button onClick={handleLogout} className="logout-button">
            로그아웃
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;