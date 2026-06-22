import React from 'react';

interface EmptyStateProps {
  title?: string;
  message: string;
  icon?: React.ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  actionDisabled?: boolean;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'Chưa có dữ liệu',
  message,
  icon = '📭',
  actionLabel,
  onAction,
  actionDisabled = false,
}) => {
  return (
    <div className="digest-empty-card">
      <span className="digest-empty-icon" role="img" aria-label="empty">{icon}</span>
      <h3>{title}</h3>
      <p>{message}</p>
      {actionLabel && onAction && (
        <button
          className="btn-run-job"
          style={{ marginTop: 16 }}
          onClick={onAction}
          disabled={actionDisabled}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};

export default EmptyState;
