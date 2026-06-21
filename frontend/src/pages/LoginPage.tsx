import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const { login, error, clearError } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setLocalError(null);

    // Frontend validation
    if (!username.trim() || !password.trim()) {
      setLocalError('Vui lòng điền đầy đủ tên đăng nhập và mật khẩu.');
      return;
    }

    setLoading(true);
    try {
      await login({ username, password });
      navigate('/dashboard');
    } catch (err: any) {
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">MA</div>
          <h1>Đăng Nhập</h1>
          <p>Hệ thống Multi-Agent tương tác bài báo AI</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {/* Error Message Alert */}
          {(localError || error) && (
            <div className="auth-error-alert">
              <span>⚠️ {localError || error}</span>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="username">Tên đăng nhập</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Nhập tên đăng nhập của bạn"
              disabled={loading}
              autoComplete="username"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Mật khẩu</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Nhập mật khẩu"
              disabled={loading}
              autoComplete="current-password"
            />
          </div>

          <button type="submit" className="btn-auth-submit" disabled={loading}>
            {loading ? (
              <>
                <span className="spinner-small"></span> Đang xử lý...
              </>
            ) : (
              'Đăng Nhập'
            )}
          </button>
        </form>

        <div className="auth-footer">
          Chưa có tài khoản? <Link to="/register" onClick={clearError}>Đăng ký ngay</Link>
        </div>
      </div>
    </div>
  );
};
