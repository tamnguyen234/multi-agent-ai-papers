import React from 'react';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Không tải được dữ liệu',
  message,
  onRetry,
  retryLabel = 'Thử lại',
}) => {
  return (
    <div className="digest-error-card">
      <span className="digest-error-icon" role="img" aria-label="warning">⚠️</span>
      <div>
        <strong>{title}</strong>
        <p>{message}</p>
      </div>
      {onRetry && (
        <button className="btn-retry" onClick={onRetry}>
          {retryLabel}
        </button>
      )}
    </div>
  );
};

export default ErrorState;
