import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { getTodayDigest, runDailyDigestJob } from '../api/digestApi';
import { getApiErrorMessage } from '../utils/apiError';
import type { DigestResponse } from '../types/digest';
import PaperDigestCard from '../components/PaperDigestCard';
import { Play, RotateCw, Calendar, Inbox } from 'lucide-react';
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

  // Run job state
  const [isRunningJob, setIsRunningJob] = useState<boolean>(false);

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

  const handleRunDigestJob = async () => {
    if (isRunningJob) return;
    setIsRunningJob(true);
    showToast('Bắt đầu tải bài báo mới từ Hugging Face...', 'info');
    try {
      const res = await runDailyDigestJob();
      showToast(res.message || `Hoàn thành! Tạo ${res.total_papers ?? '?'} bài báo mới.`, 'success');
      // Refresh digest after job
      await fetchDigest();
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
          <h1>Welcome, {currentUser?.full_name || currentUser?.username}</h1>
          <p>{today} — Daily AI Papers Digest</p>
        </div>
        <div className="welcome-actions">
          <button
            id="btn-run-digest-job"
            className={`btn-run-job${isRunningJob ? ' btn-run-job--loading' : ''}`}
            onClick={handleRunDigestJob}
            disabled={isRunningJob || digestLoading}
            title="Run Daily Digest Job"
          >
            {isRunningJob ? (
              <>
                <RotateCw className="spinner-small" size={16} /> Running...
              </>
            ) : (
              <>
                <Play size={16} /> Run Digest Job
              </>
            )}
          </button>
        </div>
      </section>

      {/* Daily Digest Section */}
      <section className="digest-section">
        <div className="digest-section__header">
          <h2 className="digest-section__title">
            Daily Top 5 AI Papers
          </h2>
          {digest && (
            <span className="digest-date-badge">
              <Calendar size={14} style={{ marginRight: '4px', display: 'inline-block', verticalAlign: 'text-bottom' }} />
              {digest.digest_date}
            </span>
          )}
          <button
            className="btn-refresh"
            onClick={fetchDigest}
            disabled={digestLoading}
            title="Refresh"
          >
            {digestLoading ? <RotateCw className="spinner-small" size={16} /> : <><RotateCw size={16} /> Refresh</>}
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
            title="No papers found for today"
            message="The system has not fetched any papers today. Run the Digest Job to fetch the latest updates."
            icon={<Inbox size={48} className="text-muted" />}
            actionLabel="Run Digest Job"
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
