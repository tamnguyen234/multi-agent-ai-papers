import React from 'react';
import { Link } from 'react-router-dom';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="placeholder-page">
      <div className="placeholder-card">
        <span className="placeholder-icon">⚠️</span>
        <h2>404 - Không Tìm Thấy Trang</h2>
        <p className="placeholder-desc">
          Đường dẫn bạn truy cập không tồn tại hoặc đã bị di chuyển.
        </p>
        <div className="placeholder-action" style={{ marginTop: '20px' }}>
          <Link to="/dashboard" className="btn-auth-submit" style={{ textDecoration: 'none', display: 'inline-block' }}>
            Quay lại Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
};
