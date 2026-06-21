import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { getTodayDigest, runDailyDigestJob } from '../api/digestApi';
import { getApiErrorMessage } from '../utils/apiError';
import type { DigestResponse } from '../types/digest';
import PaperDigestCard from '../components/PaperDigestCard';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import EmptyState from '../components/ui/EmptyState';

export const DashboardPage: React.FC = () => {
  const { currentUser } = useAuth();
  const { showToast } = useToast();

  // Digest state
  const [digest, setDigest] = useState<DigestResponse | null>(null);
  const [digestLoading, setDigestLoading] = useState<boolean>(true);
  const [digestError, setDigestError] = useState<string | null>(null);

  // Background job polling state
  const [isRunningJob, setIsRunningJob] = useState<boolean>(false);
  const [jobRunningInBackground, setJobRunningInBackground] = useState<boolean>(false);
  const pollIntervalRef = React.useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchDigest = useCallback(async () => {
    setDigestLoading(true);
    setDigestError(null);
    try {
      const data = await getTodayDigest();
      setDigest(data);
    } catch (err: unknown) {
      const message = getApiErrorMessage(err, 'Không thể tải bản tin hôm nay.');
      setDigestError(message);
    } finally {
      setDigestLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDigest();
  }, [fetchDigest]);

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  // Auto-refresh digest every 30s when job is running in background (max 5 min)
  const startPolling = () => {
    let attempts = 0;
    const MAX_ATTEMPTS = 10; // 10 × 30s = 5 minutes
    stopPolling();
    pollIntervalRef.current = setInterval(async () => {
      attempts++;
      try {
        const data = await getTodayDigest();
        setDigest(data);
        if (data && data.papers.length > 0) {
          stopPolling();
          setJobRunningInBackground(false);
          showToast('✅ Đã tải xong bài báo mới từ HuggingFace!', 'success');
        }
      } catch {
        // digest not ready yet, keep polling
      }
      if (attempts >= MAX_ATTEMPTS) {
        stopPolling();
        setJobRunningInBackground(false);
        showToast('⏱️ Job đang chạy, hãy nhấn "Làm mới" để kiểm tra kết quả.', 'info');
      }
    }, 30000);
  };

  // Cleanup on unmount
  React.useEffect(() => () => stopPolling(), []);

  const handleRunDigestJob = async () => {
    if (isRunningJob || jobRunningInBackground) return;
    setIsRunningJob(true);
    showToast('🚀 Đang khởi động Digest Job...', 'info');
    try {
      const res = await runDailyDigestJob();
      if (res.status === 'started') {
        showToast('⏳ ' + res.message, 'info');
        setJobRunningInBackground(true);
        startPolling();
      }
    } catch (err: unknown) {
      const msg = getApiErrorMessage(err, 'Chạy Digest Job thất bại.');
      showToast(msg, 'error');
    } finally {
      setIsRunningJob(false);
    }
  };


  const today = new Date().toLocaleDateString('vi-VN', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return (
    <div className="dashboard-container">
      {/* Welcome banner */}
      <section className="welcome-banner">
        <div className="welcome-content">
          <h1>Xin chào, {currentUser?.full_name || currentUser?.username}! 👋</h1>
          <p>{today} — Dưới đây là Top 5 bài báo AI hot nhất hôm nay từ HuggingFace Daily Papers.</p>
        </div>
        <div className="welcome-actions">
          <button
            id="btn-run-digest-job"
            className={`btn-run-job${(isRunningJob || jobRunningInBackground) ? ' btn-run-job--loading' : ''}`}
            onClick={handleRunDigestJob}
            disabled={isRunningJob || jobRunningInBackground || digestLoading}
            title="Kích hoạt pipeline lấy bài báo mới từ HuggingFace Daily Papers (dùng cho demo)"
          >
            {isRunningJob ? (
              <><span className="spinner-small" /> Đang khởi động…</>
            ) : jobRunningInBackground ? (
              <><span className="spinner-small" /> Đang xử lý nền…</>
            ) : (
              '▶ Chạy Digest Job'
            )}
          </button>
        </div>
      </section>

      {/* Daily Digest Section */}
      <section className="digest-section">
        <div className="digest-section__header">
          <h2 className="digest-section__title">
            📰 Daily Top 5 AI Papers
          </h2>
          {digest && (
            <span className="digest-date-badge">
              📅 {digest.digest_date}
            </span>
          )}
          <button
            className="btn-refresh"
            onClick={fetchDigest}
            disabled={digestLoading}
            title="Tải lại"
          >
            {digestLoading ? <span className="spinner-small" /> : '↺ Làm mới'}
          </button>
        </div>

        {/* Loading state */}
        {digestLoading && (
          <LoadingState message="Đang tải bản tin hôm nay..." />
        )}

        {/* Error state */}
        {!digestLoading && digestError && (
          <ErrorState message={digestError} onRetry={fetchDigest} />
        )}

        {/* Empty state */}
        {!digestLoading && !digestError && (!digest || digest.papers.length === 0) && (
          <EmptyState
            title="Chưa có bản tin hôm nay"
            message="Hệ thống chưa tải bài báo nào hôm nay. Nhấp nút dưới để chạy Digest Job và cập nhật bản tin HuggingFace mới nhất."
            icon="📭"
            actionLabel="Chạy Digest Job"
            onAction={handleRunDigestJob}
            actionDisabled={isRunningJob}
          />
        )}

        {/* Paper cards */}
        {!digestLoading && !digestError && digest && digest.papers.length > 0 && (
          <div className="digest-cards-grid">
            {[...digest.papers]
              .sort((a, b) => a.rank_position - b.rank_position)
              .map((entry) => (
                <PaperDigestCard key={entry.paper.id} entry={entry} />
              ))}
          </div>
        )}
      </section>
    </div>
  );
};
