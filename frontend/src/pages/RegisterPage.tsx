import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const RegisterPage: React.FC = () => {
  const { register, error, clearError } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setLocalError(null);

    // Front-end validation
    if (!fullName.trim() || !username.trim() || !email.trim() || !password || !confirmPassword) {
      setLocalError('Vui lòng nhập đầy đủ các trường thông tin.');
      return;
    }

    if (password.length < 6) {
      setLocalError('Mật khẩu phải chứa ít nhất 6 ký tự.');
      return;
    }

    if (password !== confirmPassword) {
      setLocalError('Mật khẩu và xác nhận mật khẩu không khớp.');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setLocalError('Định dạng Email không hợp lệ.');
      return;
    }

    setLoading(true);
    try {
      await register({
        full_name: fullName,
        username,
        email,
        password,
      });
      setSuccess(true);
      // Wait 2 seconds before redirecting to login page
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err: any) {
      console.error('Registration failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">MA</div>
          <h1>Đăng Ký</h1>
          <p>Tạo tài khoản hệ thống Multi-Agent AI Papers</p>
        </div>

        {success ? (
          <div className="auth-success-state">
            <div className="success-icon">✓</div>
            <h2>Đăng ký thành công!</h2>
            <p>Đang chuyển hướng về trang đăng nhập...</p>
          </div>
        ) : (
          <form className="auth-form" onSubmit={handleSubmit}>
            {/* Error Message Alert */}
            {(localError || error) && (
              <div className="auth-error-alert">
                <span>⚠️ {localError || error}</span>
              </div>
            )}

            <div className="form-group">
              <label htmlFor="fullName">Họ và tên</label>
              <input
                type="text"
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Nhập họ và tên thật"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="username">Tên đăng nhập (Username)</label>
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Dùng để đăng nhập hệ thống"
                disabled={loading}
                autoComplete="username"
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Nhập địa chỉ Email"
                disabled={loading}
                autoComplete="email"
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Mật khẩu</label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Ít nhất 6 ký tự"
                disabled={loading}
                autoComplete="new-password"
              />
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Xác nhận mật khẩu</label>
              <input
                type="password"
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Nhập lại mật khẩu"
                disabled={loading}
                autoComplete="new-password"
              />
            </div>

            <button type="submit" className="btn-auth-submit" disabled={loading}>
              {loading ? (
                <>
                  <span className="spinner-small"></span> Đang xử lý...
                </>
              ) : (
                'Đăng Ký'
              )}
            </button>
          </form>
        )}

        {!success && (
          <div className="auth-footer">
            Đã có tài khoản? <Link to="/login" onClick={clearError}>Đăng nhập</Link>
          </div>
        )}
      </div>
    </div>
  );
};
