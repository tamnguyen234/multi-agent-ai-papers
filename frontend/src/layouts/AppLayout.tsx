import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { userApi } from '../api/userApi';
import { getApiErrorMessage } from '../utils/apiError';
import { LayoutDashboard, FileText, TrendingUp, Bell, User } from 'lucide-react';

export const AppLayout: React.FC = () => {
  const { currentUser, logout, updateCurrentUserLocal } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [notiLoading, setNotiLoading] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleToggleNotification = async () => {
    if (!currentUser) return;
    const oldState = currentUser.noti_daily;
    const nextState = !oldState;
    
    setNotiLoading(true);
    try {
      await userApi.updateNotification(nextState);
      // Success: update Auth state immediately in local memory
      updateCurrentUserLocal({ noti_daily: nextState });
      showToast(
        nextState 
          ? 'Đã bật nhận email Daily Digest hằng ngày.' 
          : 'Đã tắt nhận email Daily Digest hằng ngày.',
        'success'
      );
    } catch (error) {
      // Failure: revert UI to original state and notify user
      updateCurrentUserLocal({ noti_daily: oldState });
      const errorMsg = getApiErrorMessage(error, 'Không thể cập nhật cài đặt nhận thông báo. Vui lòng thử lại sau.');
      showToast(errorMsg, 'error');
    } finally {
      setNotiLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="app-sidebar">
        <div className="sidebar-brand">
          <div className="brand-logo">PI</div>
          <h2>AI Paper Insight</h2>
        </div>
        
        <nav className="sidebar-nav">
          <NavLink to="/dashboard" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <LayoutDashboard className="nav-icon" size={20} />
            <span className="nav-text">Dashboard</span>
          </NavLink>
          <NavLink to="/papers" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <FileText className="nav-icon" size={20} />
            <span className="nav-text">All Papers</span>
          </NavLink>
          <NavLink to="/trends" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <TrendingUp className="nav-icon" size={20} />
            <span className="nav-text">Trend Analysis</span>
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <p>© 2026 Multi-Agent</p>
        </div>
      </aside>

      {/* Main Layout Area */}
      <div className="main-layout">
        {/* Header */}
        <header className="app-header">
          <div className="header-left">
            <span className="system-title">AI Paper Insight Dashboard</span>
          </div>

          <div className="header-right">
            {/* Notification Toggle */}
            <div 
              className="noti-toggle-container" 
              title="Receive Daily Digest emails"
            >
              <Bell size={16} className="text-muted" />
              <span className="noti-label">Daily Digest</span>
              <label className="switch" aria-label="Bật/Tắt nhận báo cáo qua email hàng ngày">
                <input
                  type="checkbox"
                  checked={currentUser?.noti_daily || false}
                  onChange={handleToggleNotification}
                  disabled={notiLoading}
                />
                <span className="slider round"></span>
              </label>
              {notiLoading && <span className="noti-spinner"></span>}
            </div>

            {/* User Profile Info */}
            <div className="user-profile">
              <span className="user-avatar">
                <User size={18} />
              </span>
              <div className="user-details">
                <span className="user-name">{currentUser?.full_name}</span>
                <span className="user-role">@{currentUser?.username}</span>
              </div>
            </div>

            {/* Logout button */}
            <button className="logout-btn" onClick={handleLogout} title="Đăng xuất">
              Đăng xuất
            </button>
          </div>
        </header>

        {/* Dynamic Nested Content */}
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
