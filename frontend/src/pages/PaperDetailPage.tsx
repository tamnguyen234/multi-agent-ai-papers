import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getPaperById, generateAudioAbstract } from '../api/paperApi';
import { getApiErrorMessage } from '../utils/apiError';
import type { Paper } from '../types/paper';
import AudioPlayer from '../components/AudioPlayer';
import { formatAuthors, formatDate, formatScore } from '../utils/formatters';
import { buildMediaUrl, externalAbsUrl } from '../utils/mediaUrl';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import EmptyState from '../components/ui/EmptyState';

export const PaperDetailPage: React.FC = () => {
  const { paperId } = useParams<{ paperId: string }>();
  const navigate = useNavigate();

  const [paper, setPaper] = useState<Paper | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [generatingAudio, setGeneratingAudio] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);


  useEffect(() => {
    if (!paperId) {
      setNotFound(true);
      setLoading(false);
      return;
    }

    let cancelled = false;
    const fetch = async () => {
      setLoading(true);
      setError(null);
      setNotFound(false);
      try {
        const data = await getPaperById(paperId);
        if (!cancelled) setPaper(data);
      } catch (err: unknown) {
        if (cancelled) return;
        const status =
          err && typeof err === 'object' && 'response' in err
            ? (err as { response?: { status?: number } }).response?.status
            : null;
        if (status === 404) {
          setNotFound(true);
        } else {
          const msg = getApiErrorMessage(err, 'Không thể tải thông tin bài báo.');
          setError(msg);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetch();
    return () => { cancelled = true; };
  }, [paperId]);

  const handleGenerateAudio = async () => {
    if (!paper) return;
    setGeneratingAudio(true);
    setAudioError(null);
    try {
      const res = await generateAudioAbstract(paper.id, {
        voice: 'vi_female',
        language: 'vi',
        force: false
      });
      
      // Update paper state dynamically supporting nested response attributes
      setPaper({
        ...paper,
        has_audio: true,
        audio_abstract: res.audio_abstract,
        audio_abstract_path: res.audio_abstract?.file_path || null,
        audio_abstract_url: res.audio_url || res.audio_abstract?.audio_url || null,
        audio_duration_seconds: res.duration_seconds || res.audio_abstract?.duration_seconds || null,
      });
    } catch (err: unknown) {
      const msg = getApiErrorMessage(err, 'Không thể tạo audio abstract.');
      setAudioError(msg);
    } finally {
      setGeneratingAudio(false);
    }
  };

  // Loading
  if (loading) {
    return <LoadingState message="Đang tải thông tin bài báo…" />;
  }

  // Not found
  if (notFound) {
    return (
      <EmptyState
        title="Không tìm thấy bài báo"
        message={`Bài báo với ID ${paperId || ''} không tồn tại hoặc đã bị xóa.`}
        icon="🔍"
        actionLabel="← Quay lại danh sách"
        onAction={() => navigate('/papers')}
      />
    );
  }

  // Error
  if (error || !paper) {
    return (
      <ErrorState
        title="Lỗi tải bài báo"
        message={error ?? 'Lỗi không xác định.'}
        onRetry={() => navigate('/papers')}
        retryLabel="Danh sách bài báo"
      />
    );
  }

  const pdfUrl = buildMediaUrl(paper.pdf_url || paper.pdf_path);
  const audioUrl = buildMediaUrl(paper.audio_abstract_url || paper.audio_abstract_path);
  const sourceUrl = paper.source_url || externalAbsUrl(paper.external_id);
  const authorsStr = formatAuthors(paper.authors);
  const dateStr = formatDate(paper.published);
  const scoreLabel = formatScore(paper.score);

  return (
    <div className="detail-page">
      {/* Back navigation */}
      <div className="detail-breadcrumb">
        <button className="btn-back" onClick={() => navigate(-1)}>
          ← Quay lại
        </button>
        <span className="breadcrumb-sep">/</span>
        <Link to="/papers" className="breadcrumb-link">Bài báo</Link>
        <span className="breadcrumb-sep">/</span>
        <span className="breadcrumb-current">Chi tiết</span>
      </div>

      {/* Title */}
      <div className="detail-header">
        <h1 className="detail-title">{paper.title}</h1>
        <div className="detail-header__chips">
          <span className="score-chip">⭐ {scoreLabel}</span>
          {pdfUrl && <span className="badge badge--pdf">📄 PDF</span>}
          {(audioUrl || paper.has_audio) && (
            <span className="badge badge--audio">🎙️ Audio</span>
          )}
        </div>
      </div>

      {/* Metadata row */}
      <div className="detail-meta">
        <div className="detail-meta__item">
          <span className="detail-meta__label">ID Nguồn</span>
          <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className="detail-meta__link">
            {paper.external_id} ↗
          </a>
        </div>
        <div className="detail-meta__item">
          <span className="detail-meta__label">Ngày đăng</span>
          <span className="detail-meta__value">{dateStr}</span>
        </div>
        <div className="detail-meta__item">
          <span className="detail-meta__label">Điểm xu hướng</span>
          <span className="detail-meta__value">{scoreLabel}</span>
        </div>
      </div>

      {/* Authors */}
      {authorsStr && authorsStr !== 'Không rõ tác giả' && (
        <section className="detail-section">
          <h2 className="detail-section__title">👤 Tác giả</h2>
          <p className="detail-authors">{authorsStr}</p>
        </section>
      )}


      {/* Abstract (EN) */}
      <section className="detail-section">
        <h2 className="detail-section__title">📋 Abstract (EN)</h2>
        <div className="detail-section__content">
          {paper.abstract_en}
        </div>
      </section>

      {/* Translated Abstract */}
      {paper.abstract_vi && (
        <section className="detail-section">
          <h2 className="detail-section__title">📝 Tóm tắt (VI)</h2>
          <div className="detail-section__content">
            {paper.abstract_vi}
          </div>
        </section>
      )}

      {/* Audio abstract */}
      <section className="detail-section">
        <h2 className="detail-section__title">🎙️ Audio Abstract</h2>
        {audioUrl ? (
          <AudioPlayer
            src={audioUrl}
            title="Audio Abstract"
            durationSeconds={paper.audio_duration_seconds}
            className="detail-audio"
          />
        ) : (
          <div className="detail-audio-generator">
            {generatingAudio ? (
              <div className="audio-loading">
                <span className="spinner-mini">⏳</span>
                <p>Đang tạo audio abstract... (có thể mất từ 30s đến 2 phút)</p>
              </div>
            ) : (
              <div className="audio-generate-action">
                <p className="audio-generate-hint">Bài báo này chưa có bản ghi âm tóm tắt AI (Audio Abstract) tiếng Việt.</p>
                <button 
                  className="btn-detail-action btn-detail-action--generate" 
                  onClick={handleGenerateAudio}
                  disabled={generatingAudio}
                  id={`generate-audio-btn-${paper.id}`}
                >
                  🎙️ Tạo audio abstract
                </button>
                {audioError && <p className="audio-error-msg">⚠️ {audioError}</p>}
              </div>
            )}
          </div>
        )}
      </section>

      {/* PDF */}
      <section className="detail-section">
        <h2 className="detail-section__title">📄 Tài liệu PDF</h2>
        {pdfUrl ? (
          <div className="detail-pdf">
            <a
              href={pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-paper-link btn-paper-link--pdf"
              id={`detail-pdf-${paper.id}`}
            >
              📄 Mở PDF trong tab mới
            </a>
            <span className="detail-pdf__hint">PDF được tải về từ máy chủ backend.</span>
          </div>
        ) : (
          <div className="detail-missing">
            <span>📭</span>
            <p>Chưa có file PDF cho bài báo này.</p>
          </div>
        )}
      </section>

      {/* Action buttons */}
      <div className="detail-actions">
        <Link
          to={`/chat/${paper.id}`}
          className="btn-detail-action btn-detail-action--chat"
          id={`detail-chat-${paper.id}`}
        >
          💬 Hỏi đáp với bài báo này
        </Link>
        <a
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-detail-action btn-detail-action--arxiv"
          id={`detail-source-${paper.id}`}
        >
          🔗 Xem nguồn gốc
        </a>
        <button
          className="btn-detail-action btn-detail-action--back"
          onClick={() => navigate('/papers')}
          id="detail-back-btn"
        >
          ← Danh sách bài báo
        </button>
      </div>
    </div>
  );
};
