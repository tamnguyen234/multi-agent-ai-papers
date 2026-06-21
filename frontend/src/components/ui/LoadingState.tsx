import React from 'react';

interface LoadingStateProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ message = 'Đang tải dữ liệu...' }) => {
  return (
    <div className="digest-loading">
      <div className="spinner" />
      <p>{message}</p>
    </div>
  );
};

export default LoadingState;
