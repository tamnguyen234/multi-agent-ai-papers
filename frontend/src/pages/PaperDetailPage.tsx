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
import { ArrowLeft, ExternalLink, TrendingUp, FileText, Mic, Users, Calendar, Hash, MessageSquare, PlayCircle, SearchX, Download } from 'lucide-react';

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
        title="Paper Not Found"
        message={`The paper with ID ${paperId || ''} does not exist or has been removed.`}
        icon={<SearchX size={48} className="text-muted" />}
        actionLabel="Back to papers"
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
          <ArrowLeft size={16} className="mr-1" /> Back
        </button>
        <span className="breadcrumb-sep">/</span>
        <Link to="/papers" className="breadcrumb-link">All Papers</Link>
        <span className="breadcrumb-sep">/</span>
        <span className="breadcrumb-current">Paper Details</span>
      </div>

      {/* Title */}
      <div className="detail-header">
        <h1 className="detail-title">{paper.title}</h1>
        <div className="detail-header__chips">
          <span className="score-chip"><TrendingUp size={14} className="mr-1" /> Score {scoreLabel}</span>
          {pdfUrl && <span className="badge badge--pdf"><FileText size={14} className="mr-1" /> PDF</span>}
          {(audioUrl || paper.has_audio) && (
            <span className="badge badge--audio"><Mic size={14} className="mr-1" /> Audio</span>
          )}
        </div>
      </div>

      {/* Metadata row */}
      <div className="detail-meta">
        <div className="detail-meta__item">
          <span className="detail-meta__label"><Hash size={14} className="mr-1" /> Source ID</span>
          <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className="detail-meta__link">
            {paper.external_id} <ExternalLink size={12} className="ml-1" />
          </a>
        </div>
        <div className="detail-meta__item">
          <span className="detail-meta__label"><Calendar size={14} className="mr-1" /> Published</span>
          <span className="detail-meta__value">{dateStr}</span>
        </div>
        <div className="detail-meta__item">
          <span className="detail-meta__label"><TrendingUp size={14} className="mr-1" /> Trend Score</span>
          <span className="detail-meta__value">{scoreLabel}</span>
        </div>
      </div>

      {/* Authors */}
      {authorsStr && authorsStr !== 'Không rõ tác giả' && (
        <section className="detail-section">
          <h2 className="detail-section__title"><Users size={18} className="mr-2" /> Authors</h2>
          <p className="detail-authors">{authorsStr}</p>
        </section>
      )}


      {/* Abstract (EN) */}
      <section className="detail-section">
        <h2 className="detail-section__title"><FileText size={18} className="mr-2" /> Original Abstract</h2>
        <div className="detail-section__content">
          {paper.abstract_en}
        </div>
      </section>

      {/* Translated Abstract */}
      {paper.abstract_vi && (
        <section className="detail-section">
          <h2 className="detail-section__title"><FileText size={18} className="mr-2" /> Vietnamese Translation</h2>
          <div className="detail-section__content">
            {paper.abstract_vi}
          </div>
        </section>
      )}

      {/* Audio abstract */}
      <section className="detail-section">
        <h2 className="detail-section__title"><Mic size={18} className="mr-2" /> Audio Abstract</h2>
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
                <span className="spinner-mini"></span>
                <p>Generating audio abstract... (this might take up to 2 minutes)</p>
              </div>
            ) : (
              <div className="audio-generate-action">
                <p className="audio-generate-hint">This paper does not have an AI-generated audio abstract yet.</p>
                <button 
                  className="btn-detail-action btn-detail-action--generate flex items-center justify-center gap-2" 
                  onClick={handleGenerateAudio}
                  disabled={generatingAudio}
                  id={`generate-audio-btn-${paper.id}`}
                >
                  <PlayCircle size={16} /> Generate Audio Abstract
                </button>
                {audioError && <p className="audio-error-msg">⚠️ {audioError}</p>}
              </div>
            )}
          </div>
        )}
      </section>

      {/* PDF */}
      <section className="detail-section">
        <h2 className="detail-section__title"><FileText size={18} className="mr-2" /> PDF Document</h2>
        {pdfUrl ? (
          <div className="detail-pdf">
            <a
              href={pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-paper-link btn-paper-link--pdf flex items-center justify-center gap-2"
              id={`detail-pdf-${paper.id}`}
            >
              <Download size={16} /> View/Download PDF
            </a>
            <span className="detail-pdf__hint">Document cached locally from backend.</span>
          </div>
        ) : (
          <div className="detail-missing">
            <FileText size={32} className="text-muted opacity-50" />
            <p>No PDF available for this paper.</p>
          </div>
        )}
      </section>

      {/* Action buttons */}
      <div className="detail-actions">
        <Link
          to={`/chat/${paper.id}`}
          className="btn-detail-action btn-detail-action--chat flex items-center justify-center gap-2"
          id={`detail-chat-${paper.id}`}
        >
          <MessageSquare size={16} /> Ask Q&A Agent
        </Link>
        <a
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-detail-action btn-detail-action--arxiv flex items-center justify-center gap-2"
          id={`detail-source-${paper.id}`}
        >
          <ExternalLink size={16} /> View External Source
        </a>
        <button
          className="btn-detail-action btn-detail-action--back flex items-center justify-center gap-2"
          onClick={() => navigate('/papers')}
          id="detail-back-btn"
        >
          <ArrowLeft size={16} /> Back to Papers
        </button>
      </div>
    </div>
  );
};
