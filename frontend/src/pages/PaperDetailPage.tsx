import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getPaperById, generateAudioAbstract, translatePaperField, synthesizeCustomText } from '../api/paperApi';
import { getApiErrorMessage } from '../utils/apiError';
import type { Paper } from '../types/paper';
import AudioPlayer from '../components/AudioPlayer';
import { formatAuthors, formatDate } from '../utils/formatters';
import { buildMediaUrl, arxivAbsUrl, hfPaperUrl } from '../utils/mediaUrl';
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

  // Translation state
  const [translatedAbstract, setTranslatedAbstract] = useState<string | null>(null);
  const [translatingAbstract, setTranslatingAbstract] = useState<boolean>(false);
  const [translateAbstractError, setTranslateAbstractError] = useState<string | null>(null);

  // Audio for translation state

  const [abstractTtsUrl, setAbstractTtsUrl] = useState<string | null>(null);
  const [generatingAbstractTts, setGeneratingAbstractTts] = useState<boolean>(false);
  const [abstractTtsError, setAbstractTtsError] = useState<string | null>(null);
  const [abstractTtsDuration, setAbstractTtsDuration] = useState<number | null>(null);

  const handleTranslateAbstract = async () => {
    if (!paper) return;
    setTranslatingAbstract(true);
    setTranslateAbstractError(null);
    try {
      const res = await translatePaperField(paper.id, 'abstract');
      setTranslatedAbstract(res.translated_text);
    } catch (err: unknown) {
      const msg = getApiErrorMessage(err, 'Không thể dịch abstract.');
      setTranslateAbstractError(msg);
    } finally {
      setTranslatingAbstract(false);
    }
  };

  const handleTtsTranslatedAbstract = async () => {
    if (!translatedAbstract) return;
    setGeneratingAbstractTts(true);
    setAbstractTtsError(null);
    try {
      const res = await synthesizeCustomText(translatedAbstract, 'vi_female');
      setAbstractTtsUrl(res.audio_url);
      setAbstractTtsDuration(res.duration_seconds);
    } catch (err: unknown) {
      const msg = getApiErrorMessage(err, 'Không thể tạo giọng đọc cho abstract.');
      setAbstractTtsError(msg);
    } finally {
      setGeneratingAbstractTts(false);
    }
  };


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
        if (!cancelled) {
          setPaper(data);
          // Pre-populate translation from DB if already exists
          if (data.abstract_vi) setTranslatedAbstract(data.abstract_vi);
          // Pre-populate TTS URL if paper already has pre-generated audio
          if (data.audio_abstract_url) {
            setAbstractTtsUrl(data.audio_abstract_url);
            setAbstractTtsDuration(data.audio_duration_seconds);
          }
        }
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
  const arxivUrl = arxivAbsUrl(paper.arxiv_id);
  const hfUrl = hfPaperUrl(paper.arxiv_id);
  const authorsStr = formatAuthors(paper.authors);
  const dateStr = formatDate(paper.published);

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
          <span className="score-chip">👍 {paper.upvotes}</span>
          {pdfUrl && <span className="badge badge--pdf">📄 PDF</span>}
          {(audioUrl || paper.has_audio) && (
            <span className="badge badge--audio">🎙️ Audio</span>
          )}
        </div>
      </div>

      {/* Metadata row */}
      <div className="detail-meta">
        <div className="detail-meta__item">
          <span className="detail-meta__label">Mã ID bài báo</span>
          <span className="detail-meta__value">{paper.arxiv_id}</span>
        </div>
        <div className="detail-meta__item">
          <span className="detail-meta__label">Ngày đăng</span>
          <span className="detail-meta__value">{dateStr}</span>
        </div>
        <div className="detail-meta__item">
          <span className="detail-meta__label">Số lượt upvote</span>
          <span className="detail-meta__value">{paper.upvotes}</span>
        </div>
      </div>

      {/* Authors */}
      {authorsStr && authorsStr !== 'Không rõ tác giả' && (
        <section className="detail-section">
          <h2 className="detail-section__title">👤 Tác giả</h2>
          <p className="detail-authors">{authorsStr}</p>
        </section>
      )}


      {/* Abstract */}
      <section className="detail-section">
        <h2 className="detail-section__title">📋 Abstract</h2>
        <div className="detail-text-block">
          {paper.abstract}
        </div>
        
        <div style={{ marginTop: '12px' }}>
          {!translatedAbstract && !translatingAbstract && (
            <button 
              className="btn-detail-action" 
              style={{ background: '#ecfdf5', color: '#059669', borderColor: '#a7f3d0' }}
              onClick={handleTranslateAbstract}
            >
              🤗 Dịch Abstract sang tiếng Việt (VinAI)
            </button>
          )}
          
          {translatingAbstract && (
            <div style={{ color: '#059669', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="spinner-mini">⏳</span> Đang dịch bằng model VinAI...
            </div>
          )}
          
          {translateAbstractError && (
            <p style={{ color: '#dc2626', fontSize: '13px' }}>⚠️ Lỗi: {translateAbstractError}</p>
          )}
          
          {translatedAbstract && (
            <div className="detail-text-block" style={{ marginTop: '12px', borderLeft: '3px solid #10b981', background: '#f0fdf4' }}>
              <h4 style={{ margin: '0 0 8px 0', color: '#047857' }}>🇻🇳 Bản dịch tiếng Việt:</h4>
              <p style={{ margin: '0 0 12px 0' }}>{translatedAbstract}</p>
              
              {abstractTtsUrl ? (
                <AudioPlayer
                  src={buildMediaUrl(abstractTtsUrl) || ''}
                  title="Nghe Abstract tiếng Việt"
                  durationSeconds={abstractTtsDuration}
                />
              ) : (
                <div>
                  {generatingAbstractTts ? (
                    <div style={{ color: '#059669', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="spinner-mini">⏳</span> Đang chuyển thành giọng đọc VieNeu...
                    </div>
                  ) : (
                    <button 
                      className="btn-detail-action"
                      style={{ background: '#f0fdf4', color: '#16a34a', borderColor: '#bbf7d0' }}
                      onClick={handleTtsTranslatedAbstract}
                    >
                      🎙️ Nghe đọc bản dịch (VieNeu)
                    </button>
                  )}
                  {abstractTtsError && (
                    <p style={{ color: '#dc2626', fontSize: '13px' }}>⚠️ Lỗi: {abstractTtsError}</p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </section>

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
          href={hfUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-detail-action btn-detail-action--hf"
          style={{
            background: '#fef3c7',
            color: '#d97706',
            borderColor: '#fde68a',
            padding: '10px 18px',
            borderRadius: '8px',
            textDecoration: 'none',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            border: '1px solid #fde68a',
            fontWeight: 500
          }}
          id={`detail-hf-${paper.id}`}
        >
          🤗 Xem trên HuggingFace
        </a>
        <a
          href={arxivUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-detail-action btn-detail-action--arxiv"
          id={`detail-arxiv-${paper.id}`}
        >
          🔗 Xem trên arXiv
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
